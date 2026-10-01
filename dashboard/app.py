"""Interactive decision dashboard for fictional immunisation programme data."""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
st.set_page_config(page_title="Health Programme Decisions", layout="wide")
st.title("Health programme performance")
st.warning(
    "Portfolio demonstration using synthetic data. These are not real Nigerian "
    "facility results or estimates of health outcomes."
)


@st.cache_data
def load_inputs():
    months = pd.read_csv(
        ROOT / "data" / "processed" / "facility_month_status.csv",
        dtype={"facility_id": str, "period": str},
    )
    months["accepted_doses"] = pd.to_numeric(months["accepted_doses"])
    months["month_start"] = pd.to_datetime(months["period"] + "-01")
    forecast = pd.read_csv(ROOT / "data" / "forecast" / "service_volume_forecast.csv")
    diagnostics = json.loads((
        ROOT / "data" / "forecast" / "model_diagnostics.json"
    ).read_text(encoding="utf-8"))
    with (ROOT / "data" / "processed" / "report_review.csv").open(
        encoding="utf-8"
    ) as source:
        reviews = pd.read_csv(source, dtype=str).fillna("")
    return months, forecast, diagnostics, reviews


try:
    all_months, forecast, diagnostics, reviews = load_inputs()
except FileNotFoundError:
    st.error("Run the validation and forecasting scripts before opening the dashboard.")
    st.stop()

areas = sorted(all_months["area"].unique())
chosen_areas = st.sidebar.multiselect("Areas", areas, default=areas)
periods = sorted(all_months["period"].unique())
start_period, end_period = st.sidebar.select_slider(
    "Reporting period", options=periods, value=(periods[0], periods[-1])
)
filtered = all_months[
    all_months["area"].isin(chosen_areas)
    & all_months["period"].between(start_period, end_period)
].copy()
if filtered.empty:
    st.info("Select at least one area and a reporting period to see results.")
    st.stop()

accepted = filtered["reporting_status"] == "accepted"
expected_count = len(filtered)
submitted_count = int((filtered["submission_count"] > 0).sum())
accepted_count = int(accepted.sum())
delivered = int(filtered.loc[accepted, "accepted_doses"].sum())
comparable_target = int(filtered.loc[accepted, "target_doses"].sum())

metric_columns = st.columns(4)
metric_columns[0].metric("Reporting completeness", f"{submitted_count / expected_count:.1%}")
metric_columns[1].metric("Accepted facility-months", f"{accepted_count} / {expected_count}")
metric_columns[2].metric("Delivered doses", f"{delivered:,}")
metric_columns[3].metric(
    "Target attainment on accepted months",
    f"{delivered / comparable_target:.1%}" if comparable_target else "n/a",
)
st.caption(
    "A submitted report can be invalid. Target attainment compares delivered "
    "doses with targets only where a valid report was accepted."
)

overview_tab, followup_tab, quality_tab, forecast_tab = st.tabs(
    ["Performance", "Follow-up", "Data quality", "Forecast"]
)

with overview_tab:
    monthly = filtered.assign(
        accepted_target=filtered["target_doses"].where(accepted, 0),
        accepted_doses=filtered["accepted_doses"].fillna(0),
        submitted=(filtered["submission_count"] > 0).astype(int),
    ).groupby("period", as_index=False).agg(
        delivered_doses=("accepted_doses", "sum"),
        accepted_target=("accepted_target", "sum"),
        submitted=("submitted", "sum"),
        expected=("facility_id", "count"),
    )
    monthly["reporting_completeness_pct"] = 100 * monthly["submitted"] / monthly["expected"]
    line = px.line(
        monthly, x="period", y=["delivered_doses", "accepted_target"],
        markers=True, labels={"value": "Doses", "period": "Month", "variable": "Series"},
        title="Delivered doses and comparable targets",
    )
    st.plotly_chart(line, width="stretch")
    st.plotly_chart(
        px.bar(
            monthly, x="period", y="reporting_completeness_pct",
            title="Reporting completeness", range_y=[0, 105],
            labels={"reporting_completeness_pct": "Percent", "period": "Month"},
        ),
        width="stretch",
    )
    st.caption("Totals are lower when a facility-month is missing or invalid.")

with followup_tab:
    followup = filtered[
        (filtered["reporting_status"] != "accepted")
        | (accepted & (filtered["accepted_doses"] < 0.8 * filtered["target_doses"]))
    ].copy()
    followup["action"] = followup.apply(
        lambda row: (
            "Request report" if row["reporting_status"] == "missing"
            else "Resolve rejected submission" if row["reporting_status"] == "invalid"
            else "Discuss low service volume"
        ),
        axis=1,
    )
    st.write(f"{len(followup)} facility-months need review under the demo rules.")
    st.dataframe(
        followup[[
            "period", "area", "facility_name", "reporting_status",
            "accepted_doses", "target_doses", "action",
        ]].sort_values(["period", "area"], ascending=[False, True]),
        width="stretch", hide_index=True,
    )
    st.caption("The 80% threshold is a demonstration review rule, not a clinical standard.")

with quality_tab:
    status_table = filtered["reporting_status"].value_counts().rename_axis(
        "status"
    ).reset_index(name="facility_months")
    st.plotly_chart(
        px.bar(status_table, x="status", y="facility_months", color="status",
               title="Facility-month data status"),
        width="stretch",
    )
    st.write("Submission decisions across the full raw dataset")
    st.dataframe(
        reviews[[
            "report_id", "facility_id", "period", "doses_delivered",
            "review_status", "issue_code",
        ]],
        width="stretch", hide_index=True,
    )
    st.caption("The review table is unfiltered so every submitted row stays auditable.")

with forecast_tab:
    chart = go.Figure()
    chart.add_trace(go.Scatter(
        x=forecast["period"], y=forecast["upper_illustrative"],
        mode="lines", line={"width": 0}, name="Illustrative upper",
        showlegend=False,
    ))
    chart.add_trace(go.Scatter(
        x=forecast["period"], y=forecast["lower_illustrative"],
        mode="lines", line={"width": 0}, fill="tonexty",
        fillcolor="rgba(57, 132, 224, 0.2)", name="Illustrative error band",
    ))
    chart.add_trace(go.Scatter(
        x=forecast["period"], y=forecast["predicted_doses"],
        mode="lines+markers", name="Predicted doses",
    ))
    chart.update_layout(title="Synthetic service volume forecast", xaxis_title="Month",
                        yaxis_title="Doses delivered")
    st.plotly_chart(chart, width="stretch")
    st.write(
        f"Selected model: **{diagnostics['selected_model']}**. "
        f"It was evaluated on {len(diagnostics['scored_holdout_months'])} "
        "complete synthetic months."
    )
    st.caption(diagnostics["limitations"])
    st.caption("Forecast is programme service volume, not vaccine demand or coverage.")
