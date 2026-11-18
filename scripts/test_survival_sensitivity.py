"""Numerical and design checks; all admissions/patient labels are synthetic."""
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
from statsmodels.duration.hazard_regression import PHReg

from survival_sensitivity import (
    BASE, CORE, GRID, SensitivityError, aalen_johansen, complete_frame,
    competing_risks, efron_score_residuals, fit_clustered_cox,
    landmark_analysis, landmark_frame, load_local_bundle, run_supplement, save_local_bundle,
    synthetic_data, validate_frame,
)


class SurvivalSensitivityTests(unittest.TestCase):
    def test_shared_loader_preserves_default_projection_and_bounds_optional_keys(self):
        import current_analysis
        from google.cloud import bigquery
        frame = pd.DataFrame({"time_to_event_days": [1., 2.], "death_event": [0, 1]})
        for include_keys in [False, True]:
            with self.subTest(include_keys=include_keys), patch("google.auth.default") as auth, patch.object(bigquery, "Client") as client:
                auth.return_value = (MagicMock(), None)
                dry, query = MagicMock(), MagicMock()
                dry.total_bytes_processed = 100
                query.result.return_value.to_dataframe.return_value = frame
                client.return_value.query.side_effect = [dry, query]
                current_analysis.load_current_data(include_cluster_keys=include_keys)
                calls = client.return_value.query.call_args_list
                expected = current_analysis.QUERY.replace("SELECT e.age", "SELECT e.subject_id,e.hadm_id,e.stay_id,e.age", 1) if include_keys else current_analysis.QUERY
                self.assertEqual([c.args[0] for c in calls], [expected, expected])
                self.assertTrue(calls[0].kwargs["job_config"].dry_run)
                self.assertEqual(calls[1].kwargs["job_config"].maximum_bytes_billed, 200_000_000)
                self.assertTrue(all(c.kwargs["location"] == "US" for c in calls))

    def test_oversized_dry_run_does_not_execute_query(self):
        import current_analysis
        from google.cloud import bigquery
        with patch("google.auth.default") as auth, patch.object(bigquery, "Client") as client:
            auth.return_value = (MagicMock(), None)
            client.return_value.query.return_value.total_bytes_processed = 200_000_001
            with self.assertRaises(ValueError): current_analysis.load_current_data(include_cluster_keys=True)
            self.assertEqual(client.return_value.query.call_count, 1)

    def test_efron_scores_sum_to_gradient_away_from_optimum_with_ties(self):
        data = complete_frame(synthetic_data(True), BASE)
        time = data.time_to_event_days.to_numpy(float)
        event = data.death_event.to_numpy(int)
        x = data[BASE].to_numpy(float)
        strata = pd.factorize(data.anchor_year_group, sort=True)[0]
        model = PHReg(time, x, status=event, strata=strata, ties="efron")
        beta = np.array([.2, .005, -.1])
        scores = efron_score_residuals(time, event, x, strata, beta)
        np.testing.assert_allclose(scores.sum(axis=0), model.score(beta), atol=1e-8)

    def test_against_independent_R_survival_reference(self):
        reference = json.loads((Path(__file__).resolve().parents[1] / "docs/SURVIVAL_SUPPLEMENTS_SYNTHETIC_CHECK.json").read_text())
        for case in reference["cases"]:
            frame = synthetic_data(case["tied_times"])
            models = {name: fit_clustered_cox(frame, covariates) for name, covariates in [("primary_refined", BASE), ("core", CORE)]}
            for item in case["R_reference_values"]:
                if item["block"].startswith("AJ/"):
                    group = int(item["block"].split("/")[1])
                    subset = frame.loc[frame.raas_pre_icu.eq(group)]
                    curve = aalen_johansen(subset.time_to_event_days, np.where(subset.death_event == 1, 1, 2), GRID)
                    actual = curve[int(item["row"]), int(item["column"]) - 1]
                else:
                    name, kind = item["block"].split("/")
                    model = models[name]
                    if kind == "beta":
                        actual = model["estimates"][item["row"]]["log_coefficient"]
                    else:
                        covariates = model["covariates"]
                        matrix = model["ordinary_covariance" if kind == "ordinary" else "patient_cluster_covariance"]
                        actual = matrix[covariates.index(item["row"])][covariates.index(item["column"])]
                self.assertAlmostEqual(actual, item["value"], delta=reference["absolute_tolerance"])

    def test_same_point_estimates_distinct_cluster_covariance(self):
        result = fit_clustered_cox(synthetic_data(True), BASE)
        self.assertGreater(result["patients_with_multiple_admissions"], 0)
        self.assertGreater(result["tied_event_sets_within_era"], 0)
        self.assertFalse(np.allclose(result["ordinary_covariance"], result["patient_cluster_covariance"]))

    def test_AJ_hand_calculation_mixed_ties_and_censoring(self):
        actual = aalen_johansen([1, 1, 1, 2], [1, 2, 0, 1], [0, 1, 2])
        np.testing.assert_allclose(actual, [[0, 0, 1], [.25, .25, .5], [.75, .25, 0]])

    def test_AJ_weights_equal_explicit_replication_and_ignore_row_order(self):
        time = np.array([1., 1., 2., 3.])
        event = np.array([1, 2, 1, 0])
        weights = np.array([2, 0, 3, 1])
        actual = aalen_johansen(time, event, [0, 1, 2, 3], weights)
        expected = aalen_johansen(np.repeat(time, weights), np.repeat(event, weights), [0, 1, 2, 3])
        np.testing.assert_allclose(actual, expected)
        np.testing.assert_allclose(actual, aalen_johansen(time[::-1], event[::-1], [0, 1, 2, 3], weights[::-1]))

    def test_bootstrap_is_deterministic_and_probability_mass_is_conserved(self):
        frame = synthetic_data(True)
        first, second = [competing_risks(frame, 20, seed=18) for _ in range(2)]
        self.assertEqual(first, second)
        reordered = competing_risks(frame.sample(frac=1, random_state=21), 20, seed=18)
        self.assertEqual(first["groups"], reordered["groups"])
        self.assertEqual(first["death_cif_difference_raas_minus_no_raas"], reordered["death_cif_difference_raas_minus_no_raas"])
        for group in first["groups"]:
            for row in group["curve"]:
                self.assertAlmostEqual(row["death_cif"] + row["discharge_cif"] + row["still_hospitalized"], 1)
                self.assertLessEqual(row["death_lower_95"], row["death_upper_95"])

    def test_landmark_boundary_unknown_death_time_and_clock_reset(self):
        frame = synthetic_data().iloc[:120].copy()
        frame["time_to_event_days"] = np.arange(120) + 2.
        frame.loc[frame.index[:4], "time_to_event_days"] = [1., .5, 1., 2.]
        frame.loc[frame.index[:4], "death_event"] = [1, 0, 0, 1]
        frame.loc[frame.index[3], "death_time_fallback_flag"] = 1
        selected, flow = landmark_frame(frame)
        self.assertEqual(flow["deaths_at_or_before_landmark"], 1)
        self.assertEqual(flow["discharges_at_or_before_landmark"], 2)
        self.assertEqual(flow["additional_fallback_deaths_excluded"], 1)
        self.assertEqual(len(selected), 116)
        np.testing.assert_allclose(selected.time_to_event_days, frame.loc[selected.index, "time_to_event_days"] - 1)

    def test_landmark_models_use_matched_complete_cases(self):
        frame = synthetic_data(True)
        frame.loc[frame.index[::17], "sofa_score"] = np.nan
        result = landmark_analysis(frame)
        a, b = result["models"].values()
        self.assertEqual((a["n"], a["events"]), (b["n"], b["events"]))
        self.assertGreater(result["eligibility"]["eligible_missing_core_covariates"], 0)

    def test_invalid_keys_flags_and_times_fail_before_analysis(self):
        for scenario in ["duplicate", "missing_key", "zero_time", "bad_event", "missing_sex"]:
            frame = synthetic_data()
            if scenario == "duplicate": frame.loc[1, "hadm_id"] = frame.loc[0, "hadm_id"]
            if scenario == "missing_key": frame.loc[0, "subject_id"] = np.nan
            if scenario == "zero_time": frame.loc[0, "time_to_event_days"] = 0
            if scenario == "bad_event": frame.loc[0, "death_event"] = 3
            if scenario == "missing_sex": frame.loc[0, "gender"] = None
            with self.subTest(scenario=scenario), self.assertRaises(SensitivityError): validate_frame(frame)

    def test_default_execution_is_synthetic_and_returns_no_row_keys(self):
        with patch("current_analysis.load_current_data", side_effect=AssertionError("Unexpected clinical access")):
            result = run_supplement("cluster")
        self.assertEqual(result["data_origin"], "fully_synthetic_not_MIMIC")
        self.assertFalse(result["clinical_records_exported"])
        def check(value):
            if isinstance(value, dict):
                self.assertFalse(set(value) & {"subject_id", "hadm_id", "stay_id"})
                for child in value.values(): check(child)
            if isinstance(value, list):
                for child in value: check(child)
        check(result)
        with self.assertRaises(SensitivityError): save_local_bundle(result, Path("docs/unapproved"), Path.cwd())

    def test_cached_local_result_rejects_changed_script(self):
        bundle = run_supplement("cluster")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "reports/local_supplements/run/aggregate_results.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(bundle))
            self.assertEqual(load_local_bundle(path, root, "cluster"), bundle)
            bundle["source_script_sha256"] = "stale"
            path.write_text(json.dumps(bundle))
            with self.assertRaises(SensitivityError): load_local_bundle(path, root, "cluster")


if __name__ == "__main__":
    unittest.main()
