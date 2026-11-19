"""Synthetic tests for rerun provenance and reviewed-output publication."""
import copy
import unittest

from current_analysis import compare_saved_results
from notebook_bq_runtime import construction_select
from notebook_publication import approved, sanitize, source_hash, output_hash


class RerunGuards(unittest.TestCase):
    def test_only_execution_metadata_can_change(self):
        reference = {"n":12, "models":{"hr":0.72}, "execution":{"job":"old"}}
        actual = copy.deepcopy(reference)
        actual["execution"] = {"job":"new"}
        self.assertTrue(compare_saved_results(reference, actual)["passed"])
        actual["models"]["hr"] = 0.73
        self.assertFalse(compare_saved_results(reference, actual)["passed"])

    def test_row_counts_and_nested_fields_are_not_ignored(self):
        self.assertFalse(compare_saved_results({"n":12},{"n":13})["passed"])
        self.assertFalse(compare_saved_results({"a":{}},{"a":{"execution":1}})["passed"])

    def test_ctas_dry_run_respects_quoted_and_commented_semicolons(self):
        query = "CREATE OR REPLACE TABLE `p.d.t` AS\n-- keep ; comment\nSELECT ';' AS x /* ; */; ASSERT true;"
        self.assertEqual(construction_select(query), "-- keep ; comment\nSELECT ';' AS x /* ; */")


class PublicationGuards(unittest.TestCase):
    def fixture(self):
        book = {"nbformat":4,"nbformat_minor":5,"metadata":{"vscode":{"private":"local"}},
                "cells":[{"id":"local-id","cell_type":"code","source":["1+1"],
                          "metadata":{"execution":{"local":"state"}},"execution_count":1,
                          "outputs":[{"output_type":"execute_result","execution_count":1,
                                      "data":{"text/plain":["2"]},"metadata":{}}]}]}
        record = {"status":"passed","notebooks":[{"notebook":"example.ipynb","status":"passed",
                  "source_sha256":source_hash(book),"output_sha256":output_hash(book)}]}
        return book, record

    def test_verified_aggregate_output_survives_without_local_metadata(self):
        book, record = self.fixture()
        self.assertTrue(approved(book, record))
        public = sanitize(book, True)
        self.assertEqual(public["cells"][0]["outputs"][0]["data"]["text/plain"],"2")
        self.assertNotIn("vscode", public["metadata"])
        self.assertEqual(public["cells"][0]["metadata"],{})
        self.assertEqual(source_hash(book), source_hash(public))
        self.assertEqual(output_hash(book), output_hash(public))

    def test_edited_source_or_output_is_stripped(self):
        for field in ["source","output"]:
            book, record = self.fixture()
            if field == "source":book["cells"][0]["source"] = "2+2"
            else:book["cells"][0]["outputs"][0]["data"]["text/plain"] = "4"
            self.assertFalse(approved(book, record))
            self.assertEqual(sanitize(book, False)["cells"][0]["outputs"],[])

    def test_error_output_is_never_approved(self):
        book, record = self.fixture()
        book["cells"][0]["outputs"] = [{"output_type":"error","ename":"ValueError","evalue":"private"}]
        self.assertFalse(approved(book, record))

    def test_unreviewed_attachments_and_custom_fields_are_removed(self):
        book, record = self.fixture()
        book['custom'] = 'local'
        book['cells'][0]['attachments'] = {'unreviewed':{'image/png':'local'}}
        public = sanitize(book, approved(book, record))
        self.assertNotIn('custom', public)
        self.assertNotIn('attachments', public['cells'][0])


if __name__ == "__main__":
    unittest.main()
