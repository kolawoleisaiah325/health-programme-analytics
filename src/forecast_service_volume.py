"""Backtest and forecast fictional monthly doses delivered, not true demand."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from statsmodels.tsa.holtwinters import ExponentialSmoothing


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = PROJECT_ROOT / "data" / "processed"
FORECAST_DIR = PROJECT_ROOT / "data" / "forecast"
METHODS = ("seasonal_naive", "ridge_trend_seasonal", "holt_winters")
TRAINING_MONTHS = 24  # Holt-Winters needs two full seasonal cycles.
BACKTEST_HORIZON = 6
FORECAST_HORIZON = 12


def model_features(start_index, count):
    """Trend and annual seasonal position, with the first month at index zero."""
    t = np.arange(start_index, start_index + count, dtype=float)
    return np.column_stack((t, np.sin(2 * np.pi * t / 12),
                            np.cos(2 * np.pi * t / 12)))


def predict(method, history, horizon):
    history = np.asarray(history, dtype=float)
    if method == "seasonal_naive":
        prediction = np.resize(history[-12:], horizon)
    elif method == "ridge_trend_seasonal":
        model = Ridge(alpha=10.0)
        model.fit(model_features(0, len(history)), history)
        prediction = model.predict(model_features(len(history), horizon))
    elif method == "holt_winters":
        model = ExponentialSmoothing(
            history, trend="add", seasonal="add", seasonal_periods=12,
            initialization_method="estimated",
        ).fit(optimized=True)
        prediction = model.forecast(horizon)
    else:
        raise ValueError(f"Unknown model: {method}")
    return np.maximum(np.asarray(prediction, dtype=float), 0)


def load_monthly_series(path):
    frame = pd.read_csv(path, dtype={"facility_id": str, "period": str})
    frame["accepted_doses"] = pd.to_numeric(frame["accepted_doses"])
    frame["month_start"] = pd.to_datetime(frame["period"] + "-01")
    facility_count = frame["facility_id"].nunique()

    # An invalid or missing report is unknown. For model fitting only, borrow
    # that facility's value from the same month in the previous year. This
    # assumption is explicit and never used as observed test truth.
    previous_values = {
        (row.facility_id, row.month_start): row.accepted_doses
        for row in frame.itertuples(index=False)
        if row.reporting_status == "accepted"
    }
    imputed = []
    for row in frame.itertuples(index=False):
        if row.reporting_status == "accepted":
            imputed.append(float(row.accepted_doses))
        else:
            previous_month = row.month_start - pd.DateOffset(years=1)
            replacement = previous_values.get((row.facility_id, previous_month))
            if replacement is None:
                raise ValueError(
                    f"No prior-year value for {row.facility_id} {row.period}"
                )
            imputed.append(float(replacement))
    frame["fit_doses"] = imputed

    monthly = frame.groupby("month_start", sort=True).agg(
        observed_doses=("accepted_doses", "sum"),
        fit_doses=("fit_doses", "sum"),
        accepted_facilities=(
            "reporting_status", lambda values: int((values == "accepted").sum())
        ),
    )
    monthly["complete"] = monthly["accepted_facilities"] == facility_count
    return frame, monthly


def month_label(timestamp):
    return timestamp.strftime("%Y-%m")


def rolling_backtest(monthly):
    """Refit at each monthly origin and score complete months up to the horizon.

    Each fit sees only months before its origin, so no future value leaks
    into training. Partial months are never scored: their observed total
    would understate service volume.
    """
    fit_series = monthly["fit_doses"].to_numpy(dtype=float)
    observed = monthly["observed_doses"].to_numpy(dtype=float)
    complete = monthly["complete"].to_numpy()
    origins = list(range(TRAINING_MONTHS, len(monthly) - BACKTEST_HORIZON + 1))
    errors = {method: [] for method in METHODS}
    scored_months = set()
    actual_total = 0.0
    for origin in origins:
        predictions = {
            method: predict(method, fit_series[:origin], BACKTEST_HORIZON)
            for method in METHODS
        }
        for step, month in enumerate(range(origin, origin + BACKTEST_HORIZON)):
            if not complete[month]:
                continue
            scored_months.add(month)
            actual_total += observed[month]
            for method in METHODS:
                errors[method].append(observed[month] - predictions[method][step])
    errors = {method: np.asarray(values) for method, values in errors.items()}
    return origins, errors, sorted(scored_months), actual_total


def run_forecast(input_path=None, output_dir=None):
    input_path = Path(input_path) if input_path else PROCESSED / "facility_month_status.csv"
    output_dir = Path(output_dir) if output_dir else FORECAST_DIR
    frame, monthly = load_monthly_series(input_path)
    expected_index = pd.date_range(monthly.index.min(), periods=len(monthly), freq="MS")
    if not monthly.index.equals(expected_index):
        raise ValueError("Reporting months must be consecutive")
    if len(monthly) < TRAINING_MONTHS + BACKTEST_HORIZON:
        raise ValueError(
            f"Need at least {TRAINING_MONTHS + BACKTEST_HORIZON} months to backtest"
        )
    if not monthly["complete"].iloc[:TRAINING_MONTHS].all():
        raise ValueError("Initial training period has incomplete reporting")

    origins, errors, scored_months, actual_total = rolling_backtest(monthly)
    if len(scored_months) < 6:
        raise ValueError("Too few complete holdout months to compare forecasts")
    candidates = {
        method: {
            "mae": round(float(np.mean(np.abs(error))), 2),
            "wape_percent": round(float(100 * np.sum(np.abs(error)) / actual_total), 2),
        }
        for method, error in errors.items()
    }
    winner = min(candidates, key=lambda method: candidates[method]["mae"])
    error_band = float(np.quantile(np.abs(errors[winner]), 0.8, method="higher"))

    future = predict(winner, monthly["fit_doses"].to_numpy(dtype=float), FORECAST_HORIZON)
    dates = pd.date_range(
        monthly.index.max() + pd.DateOffset(months=1), periods=FORECAST_HORIZON, freq="MS"
    )
    forecast_rows = pd.DataFrame({
        "period": dates.strftime("%Y-%m"),
        "predicted_doses": np.rint(future).astype(int),
        "lower_illustrative": np.rint(np.maximum(0, future - error_band)).astype(int),
        "upper_illustrative": np.rint(future + error_band).astype(int),
        "model": winner,
        "data_label": "synthetic demonstration forecast",
    })

    index = monthly.index
    holdout = index[TRAINING_MONTHS:]
    scored = [month_label(index[m]) for m in scored_months]
    excluded = [month_label(m) for m in holdout[~monthly["complete"].iloc[TRAINING_MONTHS:]]]
    scored_forecasts = len(errors[winner])
    imputed_count = int((frame["reporting_status"] != "accepted").sum())
    diagnostics = {
        "data_label": "synthetic demonstration forecast",
        "target": "doses delivered (service volume), not latent demand",
        "training_period": (
            f"{month_label(index[0])} through {month_label(index[TRAINING_MONTHS - 1])}"
        ),
        "holdout_period": f"{month_label(holdout[0])} through {month_label(holdout[-1])}",
        "backtest_design": "rolling origin, refitted monthly",
        "backtest_origins": [month_label(index[origin]) for origin in origins],
        "backtest_horizon_months": BACKTEST_HORIZON,
        "scored_forecasts": scored_forecasts,
        "scored_holdout_months": scored,
        "excluded_incomplete_holdout_months": excluded,
        "imputed_facility_months_for_refit": imputed_count,
        "candidate_scores": candidates,
        "selected_model": winner,
        "illustrative_error_band_doses": round(error_band, 2),
        "limitations": (
            f"The backtest refits each method at {len(origins)} monthly origins "
            f"and scores {scored_forecasts} forecasts of up to {BACKTEST_HORIZON} "
            f"months ahead across {len(scored)} complete synthetic months. "
            "The same backtest selected the model, so its reported error may be "
            "optimistic. Independent future validation is still needed. "
            f"The band is a descriptive range from errors up to {BACKTEST_HORIZON} "
            f"months ahead; {FORECAST_HORIZON}-month-ahead errors are likely larger, "
            "and it is not a calibrated prediction interval. "
            f"{imputed_count} missing or invalid facility-months are filled from "
            "the prior year for fitting only. Delivered doses may understate "
            "true demand."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    forecast_rows.to_csv(
        output_dir / "service_volume_forecast.csv", index=False, lineterminator="\n"
    )
    (output_dir / "model_diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return diagnostics


if __name__ == "__main__":
    print(json.dumps(run_forecast(), indent=2))
