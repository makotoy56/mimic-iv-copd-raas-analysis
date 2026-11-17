# 05 — SAS/Python validation status

Current cross-platform validation is pending an independent SAS rerun. Python coefficients are refreshed from the corrected BigQuery tables. Historical SAS coefficients are not accepted as current evidence.

The notebook requires current, matching provenance: analysis version, model specification, admission/event counts, age/duration sums, and exactly matching unique parameter keys. Missing provenance or parameter loss causes an explicit stop. No patient-level records are displayed.

SAS 07 exports primary 04a and extended-core 04c separately, with era strata, plus secondary logistic results and an aggregate manifest. The private corrected-input query is `sql/06_export_sas_validation.sql`. See [validation notes](VALIDATION_NOTES.md) for the required rerun and current scope.
