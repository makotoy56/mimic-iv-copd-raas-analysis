# 04d — Optional secondary Python logistic model

[Notebook](../notebooks/04d_python_logistic_model.ipynb)

This notebook reads explicitly projected model columns from the corrected BigQuery tables through `load_current_data()` and fits the secondary logistic model in `statsmodels`. It exports coefficients and aggregate cohort provenance under ignored `python/outputs/` paths. It does not read a private CSV or require a separate analysis service.

The primary clinical analysis remains the time-to-event Cox analysis. This optional binary-outcome parameter export is not presented as independent clinical validation.

See [the main reproduction steps](../REPRODUCIBILITY.md) and [validation notes](VALIDATION_NOTES.md).
