"""Decision dashboard for a fictional immunisation programme.

Processed records supply every number; presentation never changes source data.
"""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
TEAL = "#087F8C"
NAVY = "#294E68"
AMBER = "#B27A20"
ROSE = "#B74760"
STATUS_COLORS = {"accepted": TEAL, "missing": AMBER, "invalid": ROSE}
MODEL_NAMES = {
    "seasonal_naive": "Same month last year",
    "ridge_trend_seasonal": "Ridge trend + seasonality",
    "holt_winters": "Holt-Winters",
}

st.set_page_config(page_title="Health Programme | Performance", page_icon="✚",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{(ROOT / 'dashboard' / 'style.css').read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True)


@st.cache_data
def load_inputs(file_versions):
    """File modification times invalidate the cache after a pipeline refresh."""
    months = pd.read_csv(ROOT / "data/processed/facility_month_status.csv",
                         dtype={"facility_id": str, "period": str})
    months["accepted_doses"] = pd.to_numeric(months["accepted_doses"])
    forecast = pd.read_csv(ROOT / "data/forecast/service_volume_forecast.csv")
    diagnostics = json.loads((ROOT / "data/forecast/model_diagnostics.json").read_text(
        encoding="utf-8"))
    reviews = pd.read_csv(ROOT / "data/processed/report_review.csv", dtype=str).fillna("")
    return months, forecast, diagnostics, reviews


def chart_style(figure, height=310):
    """Shared readable axes, typography and spacing for every chart."""
    figure.update_layout(
        template="plotly_white", height=height,
        margin=dict(l=10, r=20, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=12, color="#53697C"),
        legend=dict(orientation="h", y=1.16, x=0, font=dict(size=11)),
        hovermode="x unified",
    )
    figure.update_xaxes(showgrid=False, zeroline=False)
    figure.update_yaxes(gridcolor="#E7EDF2", zeroline=False, rangemode="tozero")
    return figure


def show_chart(figure):
    st.plotly_chart(figure, width="stretch", theme=None,
                    config={"displayModeBar": False, "scrollZoom": False})


def monthly_totals(frame):
    """Only accepted rows contribute doses and comparable targets."""
    accepted = frame["reporting_status"].eq("accepted")
    prepared = frame.assign(
        comparable_target=frame["target_doses"].where(accepted),
        accepted=accepted.astype(int),
        submitted=frame["submission_count"].gt(0).astype(int),
    )
    # min_count=1 preserves an unknown total when no valid reports exist.
    return prepared.groupby("period", as_index=False).agg(
        delivered=("accepted_doses", lambda values: values.sum(min_count=1)),
        target=("comparable_target", lambda values: values.sum(min_count=1)),
        accepted=("accepted", "sum"), submitted=("submitted", "sum"),
        expected=("facility_id", "count"),
    )


def export_csv(frame):
    """Carry the synthetic label into downloads as well as the on-screen view."""
    return frame.assign(data_label="synthetic demonstration data").to_csv(index=False).encode("utf-8")


try:
    paths = [ROOT / relative for relative in (
        "data/processed/facility_month_status.csv", "data/forecast/service_volume_forecast.csv",
        "data/forecast/model_diagnostics.json", "data/processed/report_review.csv",
    )]
    all_months, forecast, diagnostics, reviews = load_inputs(
        tuple(path.stat().st_mtime_ns for path in paths))
except FileNotFoundError:
    st.error("Programme data is unavailable. Run run_all.py from the project folder, then reload.")
    st.stop()

areas = sorted(all_months["area"].unique())
periods = sorted(all_months["period"].unique())
st.session_state.setdefault("areas", areas)


def reset_filters():
    st.session_state["areas"] = areas
    # Removing the slider's saved value restores its default two-ended range.
    st.session_state.pop("period", None)


with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark">✚</div><div>'
                '<div class="brand-name">Health Programme</div>'
                '<div class="brand-sub">PERFORMANCE & DECISIONS</div></div></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="sidebar-label">PROGRAMME</div>'
                '<div class="programme-name">Routine immunisation</div>', unsafe_allow_html=True)
    st.caption("Fictional facility network")
    st.markdown('<div class="sidebar-label">EXPLORE YOUR DATA</div>', unsafe_allow_html=True)
    chosen_areas = st.multiselect("Areas", areas, key="areas")
    start_period, end_period = st.select_slider(
        "Reporting period", options=periods, value=(periods[0], periods[-1]), key="period")
    st.button("Reset filters", on_click=reset_filters, width="stretch")
    st.markdown('<div class="sidebar-note"><strong>About this workspace</strong><br>'
                'Six fictional facilities, January 2023–December 2025.<br><br>'
                'Use the tabs to review performance, resolve data gaps and explore the forecast.'
                '</div>', unsafe_allow_html=True)

filtered = all_months[
    all_months["area"].isin(chosen_areas) & all_months["period"].between(start_period, end_period)
].copy()
st.markdown('<div class="eyebrow">IMMUNISATION / PROGRAMME MONITOR</div>', unsafe_allow_html=True)
st.title("Health programme performance")
header_text, header_action = st.columns([4, 1])
with header_text:
    start_label = pd.Period(start_period).strftime("%b %Y")
    end_label = pd.Period(end_period).strftime("%b %Y")
    st.caption(f"{start_label} — {end_label}  ·  {filtered['facility_id'].nunique()} facilities  ·  "
               f"{len(chosen_areas)} areas selected")
with header_action:
    st.download_button("Export view ↓", export_csv(filtered),
                       file_name=f"synthetic_programme_{start_period}_{end_period}.csv",
                       mime="text/csv", disabled=filtered.empty, width="stretch")
st.markdown('<div class="dataset-note"><strong>SYNTHETIC DATA</strong>'
            '<span>Portfolio demonstration. Figures describe fictional health facilities.</span>'
            '</div>', unsafe_allow_html=True)

if filtered.empty:
    st.info("Select at least one area and a reporting period to see results.")
    st.stop()

accepted = filtered["reporting_status"].eq("accepted")
expected_count = len(filtered)
submitted_count = int(filtered["submission_count"].gt(0).sum())
accepted_count = int(accepted.sum())
delivered = int(filtered.loc[accepted, "accepted_doses"].sum())
comparable_target = int(filtered.loc[accepted, "target_doses"].sum())
missing_count = int(filtered["reporting_status"].eq("missing").sum())
invalid_count = int(filtered["reporting_status"].eq("invalid").sum())
low_volume = accepted & (filtered["accepted_doses"] < .8 * filtered["target_doses"])
low_count = int(low_volume.sum())
followup = filtered[~accepted | low_volume].copy()
followup["action"] = followup["reporting_status"].map({
    "missing": "Request report", "invalid": "Resolve rejected submission",
    "accepted": "Discuss low service volume",
})
followup["priority"] = followup["reporting_status"].map({"missing": 0, "invalid": 0, "accepted": 1})
followup = followup.sort_values(["priority", "period", "facility_id"], ascending=[True, False, True])

metrics = st.columns(4)
metrics[0].metric("Reporting completeness", f"{submitted_count / expected_count:.1%}",
                  help=f"{submitted_count} submitted / {expected_count} expected reports. Invalid submissions count as submitted.")
metrics[1].metric("Accepted facility-months", f"{accepted_count} / {expected_count}",
                  help="One facility-month means one facility in one reporting month. Only validated reports are accepted.")
metrics[2].metric("Delivered doses", f"{delivered:,}" if accepted_count else "Unknown",
                  help="Sum from accepted reports in this view. Missing and invalid reports have unknown doses.")
metrics[3].metric("Target attainment", f"{delivered / comparable_target:.1%}" if comparable_target else "n/a",
                  help="Delivered doses divided by targets for accepted facility-months only. This is not vaccination coverage.")

overview_tab, followup_tab, quality_tab, forecast_tab = st.tabs(
    ["Performance", "Follow-up", "Data quality", "Forecast"])

with overview_tab:
    trend_column, action_column = st.columns([2.25, 1], gap="large")
    with trend_column, st.container(border=True, key="panel_delivery"):
        st.subheader("Service delivery over time")
        st.caption("Accepted reports compared with their operational targets")
        monthly = monthly_totals(filtered)
        trend = go.Figure()
        trend.add_trace(go.Scatter(
            x=monthly["period"], y=monthly["target"], name="Comparable target",
            mode="lines", line=dict(color="#8CA1B3", width=2, dash="dot"),
            hovertemplate="Target: %{y:,.0f}<extra></extra>"))
        trend.add_trace(go.Scatter(
            x=monthly["period"], y=monthly["delivered"], name="Delivered doses",
            mode="lines+markers", line=dict(color=TEAL, width=2.5), marker=dict(size=4),
            hovertemplate="Delivered: %{y:,.0f}<extra></extra>"))
        partial = monthly[monthly["accepted"] < monthly["expected"]]
        trend.add_trace(go.Scatter(
            x=partial["period"], y=partial["delivered"], name="Incomplete month",
            mode="markers", marker=dict(color=AMBER, size=9, symbol="diamond"),
            customdata=partial[["accepted", "expected"]],
            hovertemplate="%{customdata[0]} / %{customdata[1]} accepted reports<extra></extra>"))
        chart_style(trend)
        trend.update_yaxes(title_text="Doses")
        show_chart(trend)
        st.caption("Amber markers flag partial totals. Unknown reports are excluded from both doses and targets.")
    with action_column, st.container(border=True, key="panel_priorities"):
        st.subheader("Review priorities")
        st.caption(f"{len(followup)} facility-months need follow-up")
        for count, title, detail, color in (
            (missing_count, "Missing reports", "Request the outstanding submissions", "amber"),
            (invalid_count, "Invalid reports", "Resolve rejected source records", "rose"),
            (low_count, "Below target", "Review service volume below 80%", ""),
        ):
            st.markdown(f'<div class="priority-row"><div class="priority-number {color}">{count}</div>'
                        f'<div><div class="priority-text">{title}</div>'
                        f'<div class="priority-detail">{detail}</div></div></div>', unsafe_allow_html=True)
        st.caption("Open Follow-up for the facility list. The 80% threshold is a demonstration review rule.")
    with st.container(border=True, key="panel_facilities"):
        st.subheader("Facility performance")
        st.caption("Compare delivery with targets; read reporting quality alongside performance.")
        facilities = filtered.assign(
            comparable_target=filtered["target_doses"].where(accepted), accepted=accepted.astype(int)
        ).groupby(["facility_name", "area"], as_index=False).agg(
            delivered=("accepted_doses", lambda values: values.sum(min_count=1)),
            target=("comparable_target", lambda values: values.sum(min_count=1)),
            accepted=("accepted", "sum"), expected=("period", "count"))
        facilities["attainment"] = 100 * facilities["delivered"] / facilities["target"].replace(0, float("nan"))
        facilities["reporting"] = facilities["accepted"].astype(str) + " / " + facilities["expected"].astype(str)
        max_attainment = facilities["attainment"].max()
        st.dataframe(facilities.sort_values("attainment")[[
            "facility_name", "area", "delivered", "attainment", "reporting"]],
            hide_index=True, width="stretch", column_config={
                "facility_name": "Facility", "area": "Area",
                "delivered": st.column_config.NumberColumn("Doses delivered", format="%d"),
                "attainment": st.column_config.ProgressColumn("Target attainment", format="%.1f%%", min_value=0,
                    max_value=max(100.0, float(max_attainment)) if pd.notna(max_attainment) else 100.0),
                "reporting": "Accepted / expected",
            })

with followup_tab:
    st.subheader("Turn exceptions into action")
    st.caption("Data gaps appear first, followed by accepted reports below the demonstration target threshold.")
    category = st.selectbox("Follow-up category", ["All priorities", "Missing reports", "Invalid reports", "Below target"])
    category_status = {"Missing reports": "missing", "Invalid reports": "invalid", "Below target": "accepted"}
    visible_followup = followup if category == "All priorities" else followup[
        followup["reporting_status"].eq(category_status[category])]
    st.caption(f"{len(visible_followup)} facility-months in this action list")
    if visible_followup.empty:
        st.success("No follow-up items match this selection.")
    else:
        st.dataframe(visible_followup[["period", "area", "facility_name", "reporting_status",
                                      "accepted_doses", "target_doses", "action"]],
                     hide_index=True, width="stretch", column_config={
                         "period": "Month", "area": "Area", "facility_name": "Facility",
                         "reporting_status": "Report status", "action": "Suggested action",
                         "accepted_doses": st.column_config.NumberColumn("Delivered", format="%d"),
                         "target_doses": st.column_config.NumberColumn("Target", format="%d"),
                     })
    st.download_button("Download action list ↓", export_csv(visible_followup.drop(columns="priority")),
                       file_name="synthetic_followup_actions.csv", mime="text/csv", disabled=visible_followup.empty)
    st.caption("A blank dose count is unknown. A reported zero remains zero. Review actions require programme context.")

with quality_tab:
    status_column, definition_column = st.columns([1.4, 1], gap="large")
    with status_column, st.container(border=True, key="panel_quality"):
        st.subheader("Can we trust the reporting base?")
        st.caption("Facility-month status for the current area and period selection")
        status_counts = filtered["reporting_status"].value_counts().reindex(STATUS_COLORS, fill_value=0)
        status_chart = go.Figure(go.Bar(
            x=status_counts.values, y=[name.title() for name in status_counts.index],
            orientation="h", marker_color=list(STATUS_COLORS.values()),
            text=status_counts.values, textposition="outside", cliponaxis=False,
            hovertemplate="%{y}: %{x} facility-months<extra></extra>"))
        chart_style(status_chart, 250)
        status_chart.update_layout(showlegend=False, hovermode="closest")
        status_chart.update_xaxes(title_text="Facility-months", range=[0, max(1, int(status_counts.max())) * 1.2])
        status_chart.update_yaxes(autorange="reversed", showgrid=False)
        show_chart(status_chart)
    with definition_column, st.container(border=True, key="panel_definitions"):
        st.subheader("Three different decisions")
        st.markdown("**Accepted** — a valid report is available. Its doses and target can enter performance calculations.")
        st.markdown("**Missing** — no report was submitted. Request it before interpreting performance.")
        st.markdown("**Invalid** — submissions exist, but none passed validation. Resolve the source error.")
        st.caption("Resubmissions are reconciled by selecting the latest valid report. Earlier submissions stay in the audit trail.")
    with st.expander("Full submission audit · all areas and periods", expanded=False):
        st.caption("This audit intentionally retains every source submission, including unknown facilities. Sidebar filters do not apply.")
        st.dataframe(reviews[["report_id", "facility_id", "period", "doses_delivered", "review_status", "issue_code"]],
                     hide_index=True, width="stretch")

with forecast_tab:
    st.markdown('<div class="scope-note"><strong>Programme-wide forecast</strong> · All six facilities. '
                'Area and reporting-period filters do not change this model.</div>', unsafe_allow_html=True)
    forecast_column, model_column = st.columns([2.1, 1], gap="large")
    selected = diagnostics["selected_model"]
    score = diagnostics["candidate_scores"][selected]
    with forecast_column, st.container(border=True, key="panel_forecast"):
        st.subheader("Planning the next 12 months")
        st.caption("Recorded service volume and the synthetic 2026 outlook")
        history = monthly_totals(all_months)
        history = history[history["period"].str.startswith("2025")].copy()
        history.loc[history["accepted"] < history["expected"], "delivered"] = float("nan")
        chart = go.Figure()
        chart.add_trace(go.Scatter(x=history["period"], y=history["delivered"], name="Complete observed months",
                                   mode="lines+markers", line=dict(color=NAVY, width=2), connectgaps=False))
        chart.add_trace(go.Scatter(x=forecast["period"], y=forecast["upper_illustrative"],
                                   mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
        chart.add_trace(go.Scatter(x=forecast["period"], y=forecast["lower_illustrative"],
                                   mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(8,127,140,.13)",
                                   name="Illustrative error band", hoverinfo="skip"))
        chart.add_trace(go.Scatter(x=forecast["period"], y=forecast["predicted_doses"], name="Forecast",
                                   mode="lines+markers", line=dict(color=TEAL, width=2.5), marker=dict(size=4)))
        chart_style(chart, 350)
        chart.update_yaxes(title_text="Doses delivered")
        show_chart(chart)
        st.caption("Gaps in 2025 mark incomplete reporting. The shaded range is illustrative, not a calibrated prediction interval.")
    with model_column, st.container(border=True, key="panel_model"):
        st.subheader("Model evidence")
        st.caption("Selected method")
        st.markdown(f"**{MODEL_NAMES[selected]}**")
        st.metric("Average absolute error", f"{score['mae']:.2f} doses")
        st.caption(f"{score['wape_percent']:.2f}% weighted absolute percentage error · "
                   f"{len(diagnostics['scored_holdout_months'])} complete holdout months")
        comparisons = pd.DataFrame([
            {"Method": MODEL_NAMES[name], "MAE (doses)": values["mae"]}
            for name, values in diagnostics["candidate_scores"].items()
        ]).sort_values("MAE (doses)")
        st.dataframe(comparisons, hide_index=True, width="stretch")
    with st.expander("How to interpret this forecast"):
        st.write(diagnostics["limitations"])
        st.write("Delivered doses measure recorded service volume. They do not directly measure vaccine demand, vaccination coverage or health outcomes.")
    st.download_button("Download forecast ↓", forecast.to_csv(index=False).encode("utf-8"),
                       file_name="synthetic_service_volume_forecast.csv", mime="text/csv")

st.markdown('<div class="footer-note">Health Programme Analytics · Synthetic demonstration · '
            'Targets are operational planning values. No patient records are used.</div>', unsafe_allow_html=True)
