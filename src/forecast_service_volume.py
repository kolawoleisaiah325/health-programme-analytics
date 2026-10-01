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


def model_features(start_index, count):
    """Trend and annual seasonal position, with January 2023 at index zero."""
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

    # An invalid or missing report is unknown. For a later forecast fit only,
    # borrow that facility's value from the same month in the previous year.
    # This assumption is explicit and never used as observed test truth.
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


def run_forecast(input_path=None, output_dir=None):
    input_path = Path(input_path) if input_path else PROCESSED / "facility_month_status.csv"
    output_dir = Path(output_dir) if output_dir else FORECAST_DIR
    frame, monthly = load_monthly_series(input_path)
    if len(monthly) != 36 or monthly.index.min() != pd.Timestamp("2023-01-01"):
        raise ValueError("This demonstration expects January 2023 to December 2025")

    training = monthly.iloc[:24]
    holdout = monthly.iloc[24:]
    if not training["complete"].all():
        raise ValueError("Training period has incomplete reporting")
    score_mask = holdout["complete"].to_numpy()
    if score_mask.sum() < 6:
        raise ValueError("Too few complete holdout months to compare forecasts")

    history = training["observed_doses"].to_numpy(dtype=float)
    observed = holdout["observed_doses"].to_numpy(dtype=float)[score_mask]
    candidates = {}
    predictions = {}
    for method in ("seasonal_naive", "ridge_trend_seasonal", "holt_winters"):
        all_predictions = predict(method, history, len(holdout))
        error = observed - all_predictions[score_mask]
        candidates[method] = {
            "mae": round(float(np.mean(np.abs(error))), 2),
            "wape_percent": round(float(100 * np.sum(np.abs(error)) /
                                        np.sum(observed)), 2),
        }
        predictions[method] = all_predictions
    winner = min(candidates, key=lambda method: candidates[method]["mae"])
    holdout_error = np.abs(observed - predictions[winner][score_mask])
    error_band = float(np.quantile(holdout_error, 0.8, method="higher"))

    future = predict(winner, monthly["fit_doses"].to_numpy(dtype=float), 12)
    dates = pd.date_range("2026-01-01", periods=12, freq="MS")
    forecast_rows = pd.DataFrame({
        "period": dates.strftime("%Y-%m"),
        "predicted_doses": np.rint(future).astype(int),
        "lower_illustrative": np.rint(np.maximum(0, future - error_band)).astype(int),
        "upper_illustrative": np.rint(future + error_band).astype(int),
        "model": winner,
        "data_label": "synthetic demonstration forecast",
    })
    diagnostics = {
        "data_label": "synthetic demonstration forecast",
        "target": "doses delivered (service volume), not latent demand",
        "training_period": "2023-01 through 2024-12",
        "holdout_period": "2025-01 through 2025-12",
        "scored_holdout_months": [
            month.strftime("%Y-%m") for month in holdout.index[score_mask]
        ],
        "excluded_incomplete_holdout_months": [
            month.strftime("%Y-%m") for month in holdout.index[~score_mask]
        ],
        "imputed_facility_months_for_refit": int(
            (frame["reporting_status"] != "accepted").sum()
        ),
        "candidate_scores": candidates,
        "selected_model": winner,
        "illustrative_error_band_doses": round(error_band, 2),
        "limitations": (
            "Only nine complete synthetic holdout months are scored. "
            "The same holdout selected the model, so its reported error may be "
            "optimistic. Independent future validation is still needed. "
            "The band is a descriptive error range, not a calibrated prediction "
            "interval. Missing 2025 facility values are filled from 2024 for "
            "the final fit. Delivered doses may understate true demand."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    forecast_rows.to_csv(output_dir / "service_volume_forecast.csv", index=False)
    (output_dir / "model_diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8"
    )
    return diagnostics


if __name__ == "__main__":
    print(json.dumps(run_forecast(), indent=2))
