"""Explicit input selection for 05a–05c; current data is the notebook default.

This wrapper does not implement queries or models. It delegates to the existing
bounded, read-only loader and never substitutes another input mode on failure.
"""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import re


MODES = {"current", "local", "synthetic"}
ANALYSES = {"cluster", "competing", "landmark"}
NOTEBOOK_INPUT_GUIDANCE = (
    "New execution defaults to current clinical data. The input cell announces its mode before loading. "
    "Missing configuration, credentials or access stops execution without a synthetic fallback. "
    "Choose synthetic explicitly for artificial software checks, or local explicitly for a verified saved aggregate bundle. "
    "Existing stored runtime outputs retain their earlier origin labels; changing this policy does not rerun or revalidate them.")
RUNTIME_GUIDANCE = (
    "The selected input origin is displayed once below, and again only if it changes. "
    "The default is current clinical data; configuration or access failure stops execution. "
    "Synthetic demonstrations and saved local aggregates require explicit selection. "
    "Figure 1 above remains the fixed published aggregate snapshot; stored runtime outputs retain their earlier execution labels.")
SHORT_MODE_GUIDANCE = (
    'The source notebook defaults to `DATA_MODE = "current"`, using the existing read-only, US-dry-run/200-MB-capped loader. '
    'Missing configuration, credentials or access stops execution with guidance; no synthetic fallback is used. '
    '`synthetic` must be selected explicitly for artificial software checks; `local` explicitly reads a saved, hash-verified aggregate bundle without another query. '
    'The selected mode is announced before loading; patient/admission/stay keys remain in memory. Never display admission-level rows.')
GUIDANCE = {
    "UNKNOWN_MODE": (
        "The notebook input mode is not supported.",
        "Choose current, local or synthetic explicitly in COPD_NOTEBOOK_DATA_MODE; an unset variable selects current."),
    "UNKNOWN_ANALYSIS": (
        "The requested supplement is not supported.",
        "Use cluster (05a), competing (05b) or landmark (05c)."),
    "CURRENT_CONFIGURATION_MISSING": (
        "The versioned current-data configuration or reference is missing or invalid.",
        "Run from the repository root/notebooks directory; check docs/CURRENT_ANALYSIS.json and the project/dataset/table names in scripts/current_analysis.py. Follow REPRODUCIBILITY.md."),
    "CURRENT_CREDENTIALS_MISSING": (
        "Application Default Credentials are unavailable to this notebook kernel.",
        "Configure ADC for your approved Google Cloud account as described in REPRODUCIBILITY.md, then restart the selected kernel and rerun the input cell."),
    "CURRENT_CREDENTIALS_INVALID": (
        "The current Google Cloud credentials could not be refreshed or authenticated.",
        "Renew ADC for your approved account using the reproducibility instructions, then restart the kernel and rerun the input cell."),
    "CURRENT_ACCESS_DENIED": (
        "The account lacks permission for the current-data query.",
        "Confirm the approved account has bigquery.jobs.create in the configured query project and read access to the existing ICU-COPD analysis tables."),
    "CURRENT_SOURCE_NOT_FOUND": (
        "A configured BigQuery project, dataset or analysis table was not found.",
        "Check the project/dataset/table names and US location against REPRODUCIBILITY.md. This notebook does not create or rebuild tables."),
    "CURRENT_QUERY_INVALID": (
        "BigQuery rejected the current query configuration.",
        "Check the versioned SELECT, configured source names and US location. Keep the existing dry-run and 200 MB limits."),
    "CURRENT_BYTE_LIMIT": (
        "The current SELECT exceeds the existing 200 MB processing guard.",
        "Review the configured source and bounded SELECT. Do not raise the byte limit to bypass this stop."),
    "CURRENT_REFERENCE_MISMATCH": (
        "The current source/cohort does not match the versioned analysis reference.",
        "Review the local reference checks before fitting or publishing a new result; do not replace the reference with an unverified run."),
    "CURRENT_EXECUTION_FAILED": (
        "Current-data access or validation did not complete.",
        "Check approved source access, network availability and the local validation checks. Retry only after resolving the cause; keep row-level records private."),
    "INPUT_ORIGIN_MISMATCH": (
        "The returned aggregate input does not match the selected mode.",
        "Review the selected loader and data_origin. A current run must return authorized_local_current_cohort, never synthetic results."),
    "INVALID_AGGREGATE_RESULT": (
        "The selected loader did not return the expected aggregate-only result.",
        "Review the selected supplement and its saved aggregate schema before displaying results."),
    "LOCAL_FILE_REQUIRED": (
        "Local mode requires an explicitly selected saved aggregate JSON file.",
        "Set LOCAL_RESULT to a verified bundle under reports/local_supplements, then rerun the input cell."),
    "LOCAL_FILE_NOT_FOUND": (
        "The selected local aggregate JSON file is unavailable.",
        "Check LOCAL_RESULT and select an existing verified bundle under reports/local_supplements."),
    "LOCAL_RESULT_INVALID": (
        "The local aggregate bundle failed its source/reference/schema checks.",
        "Use a matching verified aggregate bundle; keep its original provenance and source/reference hashes."),
    "DEPENDENCIES_MISSING": (
        "The selected notebook environment lacks a required analysis dependency.",
        "Run uv sync --locked and select the repository Python 3.12 kernel before retrying."),
    "INVALID_BOOTSTRAP_COUNT": (
        "The bootstrap count is invalid for the selected mode.",
        "Use an integer of at least 1000 for current data, or a positive integer for an explicit synthetic demonstration."),
    "SYNTHETIC_EXECUTION_FAILED": (
        "The explicitly selected synthetic demonstration did not complete.",
        "Check the local software environment and synthetic validation tests."),
}


class NotebookInputError(RuntimeError):
    """User-actionable fixed messages, without provider details or row values."""

    def __init__(self, code):
        self.code = code
        reason, action = GUIDANCE[code]
        super().__init__(f"{code}: {reason}\nNext: {action}\nExecution stopped; the selected input mode was not changed.")


def resolve_mode(mode=None, *, environ=None):
    settings = os.environ if environ is None else environ
    value = settings.get("COPD_NOTEBOOK_DATA_MODE", "current") if mode is None else mode
    if not isinstance(value, str) or value.strip().lower() not in MODES:
        raise NotebookInputError("UNKNOWN_MODE") from None
    return value.strip().lower()


def _error_chain(error):
    seen = set()
    while error is not None and id(error) not in seen:
        seen.add(id(error))
        yield error
        error = error.__cause__ or error.__context__


def _current_error(error):
    chain = list(_error_chain(error))
    if any(isinstance(item, ImportError) for item in chain):
        return "DEPENDENCIES_MISSING"
    # The existing loader intentionally suppresses provider messages. Inspect
    # exception types through that wrapper, never stringify provider details.
    for item in chain:
        module, name = type(item).__module__, type(item).__name__
        if module.startswith("google.auth") and name == "DefaultCredentialsError":
            return "CURRENT_CREDENTIALS_MISSING"
        if module.startswith("google.auth") and name == "RefreshError":
            return "CURRENT_CREDENTIALS_INVALID"
        if module.startswith("google.api_core"):
            if name in {"Unauthorized", "Unauthenticated"}:
                return "CURRENT_CREDENTIALS_INVALID"
            if name in {"Forbidden", "PermissionDenied"}:
                return "CURRENT_ACCESS_DENIED"
            if name == "NotFound":
                return "CURRENT_SOURCE_NOT_FOUND"
            if name == "BadRequest":
                return "CURRENT_QUERY_INVALID"
    for item in chain:
        if item.args and isinstance(item.args[0], str) and item.args[0] == "Current analysis SELECT exceeds the 200 MB limit":
            return "CURRENT_BYTE_LIMIT"
        if item.args and isinstance(item.args[0], str) and item.args[0] in {
            "REFERENCE_VERSION_MISMATCH", "REFERENCE_SOURCE_QUERY_MISMATCH", "CURRENT_COHORT_REFERENCE_MISMATCH"
        }:
            return "CURRENT_REFERENCE_MISMATCH"
    if any(isinstance(item, FileNotFoundError) for item in chain):
        return "CURRENT_CONFIGURATION_MISSING"
    return "CURRENT_EXECUTION_FAILED"


def _preflight_current(repo):
    if not (repo / "docs/CURRENT_ANALYSIS.json").is_file():
        raise NotebookInputError("CURRENT_CONFIGURATION_MISSING")
    try:
        reference = json.loads((repo / "docs/CURRENT_ANALYSIS.json").read_text())
        valid_reference = (isinstance(reference, dict) and isinstance(reference.get("analysis_version"), str)
                           and isinstance(reference.get("execution"), dict)
                           and isinstance(reference["execution"].get("query_sha256"), str))
    except (OSError, ValueError):
        raise NotebookInputError("CURRENT_CONFIGURATION_MISSING") from None
    if not valid_reference:
        raise NotebookInputError("CURRENT_CONFIGURATION_MISSING")
    source = importlib.import_module("current_analysis")
    query = getattr(source, "QUERY", None)
    if not isinstance(query, str) or not re.search(r"`[\w-]+\.[\w]+\.[\w]+`", query):
        raise NotebookInputError("CURRENT_CONFIGURATION_MISSING")


def run_notebook_supplement(analysis, *, repo, mode=None, local_result=None,
                            bootstrap_replicates=None, emit=print):
    selected = resolve_mode(mode)
    if analysis not in ANALYSES:
        raise NotebookInputError("UNKNOWN_ANALYSIS")
    descriptions = {
        "current": "CURRENT clinical data: existing read-only SELECT; US dry run and 200 MB cap. Access/configuration failure stops execution.",
        "local": "LOCAL saved aggregate JSON: explicit file selection and provenance checks; no BigQuery query.",
        "synthetic": "SYNTHETIC demonstration explicitly selected: artificial software-test results, not clinical MIMIC findings.",
    }
    emit(f"Input mode = {selected} | {descriptions[selected]}")
    repo = Path(repo)
    count = bootstrap_replicates if bootstrap_replicates is not None else (1000 if selected == "current" else 200)
    if selected != "local" and (type(count) is not int or count < (1000 if selected == "current" else 1)):
        raise NotebookInputError("INVALID_BOOTSTRAP_COUNT")
    if selected == "local" and local_result is None:
        raise NotebookInputError("LOCAL_FILE_REQUIRED")
    try:
        if selected == "current":
            _preflight_current(repo)
        api = importlib.import_module("survival_sensitivity")
        if selected == "local":
            bundle = api.load_local_bundle(local_result, repo, analysis)
        else:
            bundle = api.run_supplement(analysis, repo=repo, clinical=selected == "current",
                                        bootstrap_replicates=count)
    except NotebookInputError:
        raise
    except Exception as error:
        if isinstance(error, ImportError):
            code = "DEPENDENCIES_MISSING"
        elif selected == "current":
            code = _current_error(error)
        elif selected == "local":
            code = "LOCAL_FILE_NOT_FOUND" if isinstance(error, FileNotFoundError) else "LOCAL_RESULT_INVALID"
        else:
            code = "SYNTHETIC_EXECUTION_FAILED"
        raise NotebookInputError(code) from None
    if (not isinstance(bundle, dict) or bundle.get("clinical_records_exported") is not False
            or not isinstance(bundle.get("results"), dict) or analysis not in bundle["results"]):
        raise NotebookInputError("INVALID_AGGREGATE_RESULT")
    expected = {"current": {"authorized_local_current_cohort"},
                "synthetic": {"fully_synthetic_not_MIMIC"},
                "local": {"authorized_local_current_cohort", "fully_synthetic_not_MIMIC"}}
    if not isinstance(bundle.get("data_origin"), str) or bundle["data_origin"] not in expected[selected]:
        raise NotebookInputError("INPUT_ORIGIN_MISMATCH")
    return bundle
