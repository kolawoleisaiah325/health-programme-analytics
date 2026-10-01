# Responsible data and AI design

This repository contains fictional facilities and aggregate synthetic counts.
It contains no patient data. The generator, test data, and demonstration
findings must remain labelled synthetic when presented.

Before any use with real partner data, the programme owner should document:

1. The precise reporting purpose, each dataset's owner, and an appropriate
   lawful basis for processing. Where consent is relevant, record how it is
   obtained, managed, and withdrawn. Consent should not be assumed to be the
   only possible lawful basis.
2. Data minimisation: prefer facility-month aggregates. Avoid names,
   phone numbers, or patient identifiers in this warehouse and in AI prompts.
3. Access roles for programme staff, analysts, and partners; encryption in
   transit and at rest; audit logs; retention and deletion schedules.
4. A documented data-sharing arrangement, validation responsibilities,
   correction process, and incident escalation path for each partner.
5. Legal and privacy review under the [Nigeria Data Protection Act 2023](https://ndpc.gov.ng/download/nigeria-data-protection-act-2023)
   and current implementing guidance, with a data protection impact
   assessment where required by the actual processing context.

The local reporting assistant receives only qualitative, aggregate facts and
source IDs. Source values are rendered by application code after the model
responds. Output validation rejects obvious unsupported claims, but cannot
guarantee truth or fairness; a named human reviewer must check citations,
periods, missing data, and recommendations before sharing. Model and prompt
versions, approval decisions, and corrections should be logged for a real
deployment.

The forecast is not clinical advice. It cannot infer unique vaccinated
children, coverage, health outcomes, or true vaccine demand from delivered
dose counts alone. Performance should be reviewed across facilities and
time periods before operational use, including whether missingness differs
by area or facility type. This is a design checklist, not a legal compliance
certification.
