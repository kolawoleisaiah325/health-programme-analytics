"""Dashboard calculations, kept free of Streamlit so they can be unit-tested."""


FOLLOW_UP_ACTIONS = {
    "missing": "Request report",
    "invalid": "Resolve rejected submission",
    "accepted": "Discuss low service volume",
}


def known_sum(values):
    """Sum known values; an all-unknown group stays unknown instead of zero."""
    return values.sum(min_count=1)


def headline_metrics(frame, threshold):
    """Counts behind the four metric cards and the review priorities."""
    accepted = frame["reporting_status"].eq("accepted")
    low_volume = accepted & (frame["accepted_doses"] < threshold * frame["target_doses"])
    return {
        "expected": len(frame),
        # Invalid submissions still count as submitted.
        "submitted": int(frame["submission_count"].gt(0).sum()),
        "accepted": int(accepted.sum()),
        "delivered": int(frame.loc[accepted, "accepted_doses"].sum()),
        "comparable_target": int(frame.loc[accepted, "target_doses"].sum()),
        "missing": int(frame["reporting_status"].eq("missing").sum()),
        "invalid": int(frame["reporting_status"].eq("invalid").sum()),
        "below_threshold": int(low_volume.sum()),
    }


def followup_items(frame, threshold):
    """Data gaps first, then accepted months below the review threshold."""
    accepted = frame["reporting_status"].eq("accepted")
    low_volume = accepted & (frame["accepted_doses"] < threshold * frame["target_doses"])
    items = frame[~accepted | low_volume].copy()
    items["action"] = items["reporting_status"].map(FOLLOW_UP_ACTIONS)
    items["priority"] = items["reporting_status"].map({"missing": 0, "invalid": 0, "accepted": 1})
    return items.sort_values(["priority", "period", "facility_id"], ascending=[True, False, True])


def monthly_totals(frame):
    """Only accepted rows contribute doses and comparable targets."""
    accepted = frame["reporting_status"].eq("accepted")
    prepared = frame.assign(
        comparable_target=frame["target_doses"].where(accepted),
        accepted=accepted.astype(int),
        submitted=frame["submission_count"].gt(0).astype(int),
    )
    return prepared.groupby("period", as_index=False).agg(
        delivered=("accepted_doses", known_sum),
        target=("comparable_target", known_sum),
        accepted=("accepted", "sum"), submitted=("submitted", "sum"),
        expected=("facility_id", "count"),
    )


def facility_performance(frame):
    """Per-facility delivery, comparable-target attainment and reporting."""
    accepted = frame["reporting_status"].eq("accepted")
    facilities = frame.assign(
        comparable_target=frame["target_doses"].where(accepted), accepted=accepted.astype(int)
    ).groupby(["facility_name", "area"], as_index=False).agg(
        delivered=("accepted_doses", known_sum),
        target=("comparable_target", known_sum),
        accepted=("accepted", "sum"), expected=("period", "count"))
    facilities["attainment"] = (
        100 * facilities["delivered"] / facilities["target"].replace(0, float("nan"))
    )
    facilities["reporting"] = (
        facilities["accepted"].astype(str) + " / " + facilities["expected"].astype(str)
    )
    return facilities.sort_values("attainment")


def export_csv(frame):
    """Carry the synthetic label into downloads as well as the on-screen view."""
    return frame.assign(data_label="synthetic demonstration data").to_csv(
        index=False, lineterminator="\n"
    ).encode("utf-8")
