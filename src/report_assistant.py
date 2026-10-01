"""Draft a cited programme brief with a local LLM and strict claim checks."""

import argparse
import csv
import json
import re
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "reports"


def evidence_pack():
    processed = PROJECT_ROOT / "data" / "processed"
    forecast = PROJECT_ROOT / "data" / "forecast"
    summary = json.loads((processed / "quality_summary.json").read_text(encoding="utf-8"))
    diagnostics = json.loads((forecast / "model_diagnostics.json").read_text(
        encoding="utf-8"
    ))
    with (processed / "facility_month_status.csv").open(
        newline="", encoding="utf-8"
    ) as source:
        months = list(csv.DictReader(source))
    incomplete = [
        f"{r['facility_id']} {r['period']}: {r['reporting_status']}"
        for r in months if r["reporting_status"] != "accepted"
    ]
    low_performance = [
        r for r in months
        if r["period"].startswith("2025-")
        and r["reporting_status"] == "accepted"
        and int(r["accepted_doses"]) < 0.8 * int(r["target_doses"])
    ]
    return {
        "E1": {
            "fact": (
                f"{summary['submitted_facility_months']} of "
                f"{summary['expected_facility_months']} expected facility-months "
                "had a submitted report."
            ),
            "source": "data/processed/quality_summary.json",
        },
        "E2": {
            "fact": (
                f"Accepted: {summary['reporting_status_counts']['accepted']}; "
                f"missing: {summary['reporting_status_counts']['missing']}; "
                f"invalid: {summary['reporting_status_counts']['invalid']}."
            ),
            "source": "data/processed/quality_summary.json",
        },
        "E3": {
            "fact": "Unresolved facility-months: " + "; ".join(incomplete) + ".",
            "source": "data/processed/facility_month_status.csv",
        },
        "E4": {
            "fact": (
                f"{len(low_performance)} accepted facility-months in 2025 "
                "were below 80% of their dose target."
            ),
            "source": "data/processed/facility_month_status.csv",
        },
        "E5": {
            "fact": (
                f"Forecast method: {diagnostics['selected_model']}; "
                f"holdout MAE: "
                f"{diagnostics['candidate_scores'][diagnostics['selected_model']]['mae']} "
                f"doses across {len(diagnostics['scored_holdout_months'])} "
                "complete synthetic months."
            ),
            "source": "data/forecast/model_diagnostics.json",
        },
    }


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "maxLength": 180},
        "summary_evidence_ids": {"type": "array", "items": {"type": "string"}},
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "maxLength": 160},
                    "evidence_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "evidence_ids"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "summary_evidence_ids", "actions"],
    "additionalProperties": False,
}


def validate_draft(draft, evidence):
    """Reject uncited or numerical LLM claims before writing a report."""
    if not isinstance(draft, dict):
        raise ValueError("Draft must be an object")
    if set(draft) != {"summary", "summary_evidence_ids", "actions"}:
        raise ValueError("Unexpected draft fields")
    actions = draft["actions"]
    if not isinstance(actions, list) or not 1 <= len(actions) <= 4:
        raise ValueError("Draft needs one to four actions")
    items = [(draft["summary"], draft["summary_evidence_ids"])]
    for action in actions:
        if not isinstance(action, dict) or set(action) != {"text", "evidence_ids"}:
            raise ValueError("Action has unexpected fields")
        items.append((action["text"], action["evidence_ids"]))
    for text, citations in items:
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 300:
            raise ValueError("Draft text is empty or too long")
        if re.search(r"\d", text):
            raise ValueError("LLM may not invent or restate numbers")
        if re.search(r"\b(caused by|proves|guarantees|will prevent)\b", text, re.I):
            raise ValueError("Draft makes an unsupported causal or outcome claim")
        if (
            not isinstance(citations, list) or not citations
            or any(citation not in evidence for citation in citations)
        ):
            raise ValueError("Every claim needs known evidence IDs")
    return draft


def local_llm_draft(evidence, model, endpoint):
    qualitative_evidence = {
        "E1": "Most expected facility-months have a submitted report.",
        "E2": "A small number of facility-months are missing or invalid.",
        "E3": "Specific missing and invalid reports need facility follow-up.",
        "E4": "Some accepted facility-months have low service volume against targets.",
        "E5": "A synthetic service-volume forecast was backtested with limited data.",
    }
    if set(evidence) != set(qualitative_evidence):
        raise ValueError("Evidence IDs changed without updating the LLM brief")
    prompt = (
        "Use only the evidence JSON below. Write a concise programme summary "
        "and two or three management actions. Summary: one sentence, at most "
        "180 characters. Each action: one sentence, at most 160 characters. "
        "Put evidence IDs only in the evidence_ids arrays, never in prose. "
        "Do not write any digits or numeric values: the application will render "
        "exact numbers from source data. Do not infer causes, health outcomes, "
        "or real-world impact. Treat the data as fictional. Return JSON only.\n\n"
        + json.dumps(qualitative_evidence, indent=2)
    )
    payload = {
        "model": model,
        "stream": False,
        "format": OUTPUT_SCHEMA,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": "You draft cautious, cited health programme reports."},
            {"role": "user", "content": prompt},
        ],
    }
    request = Request(
        endpoint.rstrip("/") + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=180) as response:
        result = json.load(response)
    return json.loads(result["message"]["content"])


def safe_fallback():
    return {
        "summary": "Reporting is mostly complete, with a small number of records needing review.",
        "summary_evidence_ids": ["E1", "E2"],
        "actions": [
            {
                "text": "Request outstanding reports and resolve rejected submissions before drawing conclusions.",
                "evidence_ids": ["E2", "E3"],
            },
            {
                "text": "Discuss low service volume with facility teams and check local context.",
                "evidence_ids": ["E4"],
            },
            {
                "text": "Use the forecast only for scenario planning until it is tested on real data.",
                "evidence_ids": ["E5"],
            },
        ],
    }


def render_markdown(draft, evidence, generation_method):
    lines = [
        "# Draft programme decision brief",
        "",
        "**Synthetic demonstration data | Human review required before use**",
        "",
        f"Generation method: {generation_method}.",
        "",
        "## Evidence checked from source files",
        "",
    ]
    for evidence_id, item in evidence.items():
        lines.append(f"- **{evidence_id}:** {item['fact']} Source: `{item['source']}`.")
    lines.extend([
        "", "## Interpretation", "",
        draft["summary"] + " " + " ".join(
            f"[{item}]" for item in draft["summary_evidence_ids"]
        ),
        "", "## Recommended review actions", "",
    ])
    for action in draft["actions"]:
        citations = " ".join(f"[{item}]" for item in action["evidence_ids"])
        lines.append(f"- {action['text']} {citations}")
    lines.extend([
        "", "## Review checklist", "",
        "- Confirm source period, facility definitions, and target definitions.",
        "- Check each recommendation against the cited record and local context.",
        "- Do not treat delivered doses as unique children, coverage, or latent demand.",
        "- Approve or edit this draft with a named human reviewer before sharing.",
        "",
    ])
    return "\n".join(lines)


def build_report(model="llama3.2:latest", endpoint="http://localhost:11434", offline=False):
    evidence = evidence_pack()
    method = "deterministic fallback"
    failure_reason = None
    if offline:
        draft = safe_fallback()
    else:
        try:
            draft = validate_draft(local_llm_draft(evidence, model, endpoint), evidence)
            method = f"local Ollama model {model} with output validation"
        except (URLError, TimeoutError, ValueError, KeyError, TypeError) as error:
            failure_reason = f"{type(error).__name__}: {error}"
            draft = safe_fallback()
    validate_draft(draft, evidence)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "programme_brief.md").write_text(
        render_markdown(draft, evidence, method), encoding="utf-8"
    )
    validation = {
        "generation_method": method,
        "llm_failure_reason": failure_reason,
        "schema_and_citation_validation": "passed",
        "numeric_claims": "rendered only from source evidence",
        "human_review_required": True,
    }
    (OUTPUT_DIR / "assistant_validation.json").write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8"
    )
    return validation


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="llama3.2:latest")
    parser.add_argument("--endpoint", default="http://localhost:11434")
    parser.add_argument("--offline", action="store_true")
    options = parser.parse_args()
    print(json.dumps(build_report(options.model, options.endpoint, options.offline), indent=2))
