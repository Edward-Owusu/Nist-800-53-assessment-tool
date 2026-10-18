import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grc_assess import assess, load_catalog, load_rules  # noqa: E402
from grc_assess.checks import FAIL, NOT_APPLICABLE, NOT_ASSESSED, PASS, apply_op, evaluate  # noqa: E402
from grc_assess.cli import main  # noqa: E402
from grc_assess.engine import risk_rating  # noqa: E402
from grc_assess.reporting import WRITERS  # noqa: E402

WEAK = ROOT / "samples" / "example_manufacturer_weak.json"
MATURE = ROOT / "samples" / "example_cold_storage_mature.json"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class TestOperators(unittest.TestCase):
    def test_basic_operators(self):
        self.assertTrue(apply_op("gte", 12, 12))
        self.assertFalse(apply_op("lte", 31, 30))
        self.assertTrue(apply_op("between", 5, [1, 5]))
        self.assertFalse(apply_op("between", 0, [1, 5]))
        self.assertTrue(apply_op("in", "1.3", ["1.2", "1.3"]))
        self.assertTrue(apply_op("contains_none", [443], [22, 3389]))
        self.assertFalse(apply_op("contains_none", [443, 3389], [22, 3389]))
        self.assertTrue(apply_op("is_empty", [], None))

    def test_wrong_type_fails_instead_of_crashing(self):
        self.assertFalse(apply_op("gte", "twelve", 12))

    def test_unknown_operator_raises(self):
        with self.assertRaises(ValueError):
            apply_op("approximately", 1, 1)


class TestChecks(unittest.TestCase):
    def test_value_check_missing_data_is_not_assessed(self):
        out = evaluate({}, {"type": "value", "path": "logging.retention_days", "op": "gte", "value": 90})
        self.assertEqual(out.status, NOT_ASSESSED)

    def test_each_check_lists_failing_items(self):
        cfg = {"accounts": [
            {"user": "a", "admin": True, "mfa": True},
            {"user": "b", "admin": True, "mfa": False},
            {"user": "c", "admin": False, "mfa": False},
        ]}
        check = {"type": "each", "collection": "accounts", "where": {"admin": True},
                 "field": "mfa", "op": "eq", "value": True, "item_label": "user"}
        out = evaluate(cfg, check)
        self.assertEqual(out.status, FAIL)
        self.assertEqual(out.failing_items, ["b"])

    def test_each_check_missing_field_counts_as_not_evidenced(self):
        cfg = {"assets": [{"hostname": "x"}]}
        check = {"type": "each", "collection": "assets", "field": "logging_enabled",
                 "op": "eq", "value": True, "item_label": "hostname"}
        out = evaluate(cfg, check)
        self.assertEqual(out.status, FAIL)
        self.assertIn("not evidenced", out.failing_items[0])

    def test_each_check_with_no_items_in_scope_is_not_applicable(self):
        cfg = {"assets": [{"hostname": "x", "sensitive": False}]}
        check = {"type": "each", "collection": "assets", "where": {"sensitive": True},
                 "field": "encrypted", "op": "eq", "value": True}
        self.assertEqual(evaluate(cfg, check).status, NOT_APPLICABLE)

    def test_ratio_check(self):
        cfg = {"accounts": [{"admin": True}] + [{"admin": False}] * 9}
        check = {"type": "ratio", "collection": "accounts", "where": {"admin": True}, "op": "lte", "value": 0.10}
        self.assertEqual(evaluate(cfg, check).status, PASS)
        cfg["accounts"].append({"admin": True})
        self.assertEqual(evaluate(cfg, check).status, FAIL)


class TestCatalogAndRules(unittest.TestCase):
    def test_every_rule_maps_to_known_controls(self):
        catalog = load_catalog()
        rules = load_rules(catalog=catalog)  # raises if a rule references an unknown control
        self.assertGreater(len(rules), 20)

    def test_baselines_are_nested(self):
        catalog = load_catalog()
        low = set(catalog.for_baseline("low"))
        moderate = set(catalog.for_baseline("moderate"))
        high = set(catalog.for_baseline("high"))
        self.assertTrue(low <= moderate <= high)
        self.assertNotIn("AC-6", low)
        self.assertIn("AC-6", moderate)


class TestAssessment(unittest.TestCase):
    def test_weak_sample_has_critical_findings(self):
        result = assess(load(WEAK), baseline="moderate")
        severities = {f.severity for f in result.findings}
        self.assertIn("critical", severities)
        self.assertIn(result.risk_rating, {"High", "Critical"})
        ids = {f.rule_id for f in result.findings}
        self.assertIn("IAM-01", ids)   # admins without MFA
        self.assertIn("NET-01", ids)   # RDP exposed on ERP01

    def test_mature_sample_scores_low_risk(self):
        result = assess(load(MATURE), baseline="moderate")
        self.assertEqual(result.risk_rating, "Low")
        self.assertGreaterEqual(result.compliance_pct, 90)

    def test_low_baseline_excludes_moderate_only_controls(self):
        result = assess(load(WEAK), baseline="low")
        control_ids = {c.control_id for c in result.controls}
        self.assertNotIn("AC-6", control_ids)
        self.assertNotIn("IAM-05", {r.rule_id for r in result.rules})  # maps only to AC-6

    def test_findings_sorted_by_severity(self):
        order = ["critical", "high", "medium", "low"]
        sevs = [order.index(f.severity) for f in assess(load(WEAK)).findings]
        self.assertEqual(sevs, sorted(sevs))

    def test_empty_config_is_not_rated(self):
        result = assess({}, baseline="moderate")
        self.assertIsNone(result.compliance_pct)
        self.assertEqual(result.risk_rating, "Not rated")

    def test_invalid_baseline(self):
        with self.assertRaises(ValueError):
            assess({}, baseline="extreme")

    def test_risk_bands(self):
        self.assertEqual(risk_rating(0), "Low")
        self.assertEqual(risk_rating(10), "Moderate")
        self.assertEqual(risk_rating(25), "High")
        self.assertEqual(risk_rating(50), "Critical")
        self.assertEqual(risk_rating(100), "Critical")


class TestReportingAndCli(unittest.TestCase):
    def test_all_writers_produce_output(self):
        result = assess(load(WEAK))
        for fmt, writer in WRITERS.items():
            self.assertTrue(writer(result).strip(), fmt)
        json.loads(WRITERS["json"](result))  # valid JSON

    def test_html_escapes_untrusted_values(self):
        cfg = load(WEAK)
        cfg["organization"]["name"] = "<script>alert(1)</script>"
        html = WRITERS["html"](assess(cfg))
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_cli_writes_reports_and_fail_on(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = main([str(WEAK), "--format", "html", "csv", "--out", tmp, "--fail-on", "critical"])
            self.assertEqual(code, 2)
            self.assertTrue(any(Path(tmp).glob("*.html")))
            self.assertEqual(main([str(MATURE), "--out", tmp, "--fail-on", "high"]), 0)


class TestScoreExplanation(unittest.TestCase):
    def test_breakdown_adds_up_to_headline_score(self):
        result = assess(load(WEAK))
        lines = result.score_breakdown
        self.assertEqual(sum(s.failed_weight for s in lines), result.failed_weight)
        self.assertEqual(sum(s.total_weight for s in lines), result.total_weight)
        self.assertAlmostEqual(result.risk_score, round(100 * result.failed_weight / result.total_weight, 1))
        self.assertIn(f"{result.risk_score:.1f}", result.score_explanation)
        self.assertIn(result.risk_rating, result.score_explanation)

    def test_reports_explain_the_score(self):
        result = assess(load(WEAK))
        for fmt in ("md", "html"):
            self.assertIn("How the risk score is calculated", WRITERS[fmt](result))
        self.assertIn("score_explanation", json.loads(WRITERS["json"](result)))


class TestOrganizationDefinedParameters(unittest.TestCase):
    def test_defaults_are_listed(self):
        result = assess(load(WEAK))
        params = {p.rule_id: p for p in result.parameters}
        self.assertEqual(params["IAM-03"].value, 90)
        self.assertFalse(params["IAM-03"].customized)

    def test_override_changes_check_title_and_result(self):
        cfg = load(WEAK)
        strict = {r.rule_id: r for r in assess(cfg, parameters={"IAM-07": 8}).rules}
        self.assertEqual(strict["IAM-07"].status, PASS)          # sample uses 8 characters
        self.assertIn("8 characters", strict["IAM-07"].title)
        default = {r.rule_id: r for r in assess(cfg).rules}
        self.assertEqual(default["IAM-07"].status, FAIL)

    def test_percent_parameter(self):
        cfg = load(WEAK)
        rules = {r.rule_id: r for r in assess(cfg, parameters={"IAM-05": 40}).rules}
        self.assertEqual(rules["IAM-05"].status, PASS)
        self.assertIn("40%", rules["IAM-05"].title)

    def test_parameters_from_config_file(self):
        cfg = load(WEAK)
        cfg["parameters"] = {"IAM-07": 8}
        rules = {r.rule_id: r for r in assess(cfg).rules}
        self.assertEqual(rules["IAM-07"].status, PASS)

    def test_invalid_parameters_are_rejected(self):
        with self.assertRaises(ValueError):
            assess(load(WEAK), parameters={"IAM-07": 2})       # below minimum
        with self.assertRaises(ValueError):
            assess(load(WEAK), parameters={"IAM-01": 5})       # check has no parameter
        with self.assertRaises(ValueError):
            assess(load(WEAK), parameters={"XYZ-99": 5})       # unknown check


class TestPartialImplementation(unittest.TestCase):
    def test_control_in_place_but_below_target_is_partial(self):
        controls = {c.control_id: c.status for c in assess(load(WEAK)).controls}
        self.assertEqual(controls["AC-6"], "Partially implemented")    # 33% privileged vs 10% target
        self.assertEqual(controls["IA-5"], "Partially implemented")    # 8-character minimum vs 12

    def test_absent_control_stays_not_implemented(self):
        controls = {c.control_id: c.status for c in assess(load(WEAK)).controls}
        self.assertEqual(controls["IA-2(1)"], "Not implemented")      # no admin has MFA
        self.assertEqual(controls["SI-4"], "Not implemented")         # no central monitoring

    def test_each_check_with_some_compliant_items_is_partial(self):
        cfg = {"a": [{"id": 1, "ok": True}, {"id": 2, "ok": False}]}
        out = evaluate(cfg, {"type": "each", "collection": "a", "field": "ok", "op": "eq", "value": True})
        self.assertEqual(out.status, FAIL)
        self.assertTrue(out.partial)
        cfg = {"a": [{"id": 1, "ok": False}]}
        self.assertFalse(evaluate(cfg, {"type": "each", "collection": "a", "field": "ok",
                                        "op": "eq", "value": True}).partial)


class TestFamilyCoverage(unittest.TestCase):
    def test_thin_families_are_flagged(self):
        fams = {f.family: f for f in assess(load(MATURE)).families}
        self.assertTrue(fams["RA"].limited_coverage)
        self.assertEqual(fams["RA"].passed_text, "1 of 1")
        self.assertIn("Limited", fams["RA"].coverage_note)
        self.assertFalse(fams["AC"].limited_coverage)


class TestGuidedForm(unittest.TestCase):
    def test_build_config_from_answers(self):
        from grc_assess.guided import build_config
        cfg = build_config(
            {"name": "Clinic", "sector": "Health"},
            {"identity.password_policy.min_length": 10, "logging.centralized_siem": "No",
             "network.firewall_default_deny": "Don't know", "governance.training_completion_rate": 80},
            accounts=[{"username": "admin", "enabled": True, "privileged": True, "mfa_enabled": False,
                       "days_since_last_login": 2.0, "shared": False},
                      {"username": "", "enabled": True}],
            assets=[{"hostname": "PC1", "type": "workstation", "public_ports": "22, 3389",
                     "unnecessary_services": "", "max_critical_patch_age_days": float("nan")}],
        )
        self.assertEqual(cfg["identity"]["password_policy"]["min_length"], 10)
        self.assertIs(cfg["logging"]["centralized_siem"], False)
        self.assertNotIn("network", cfg)                                 # "Don't know" is left out
        self.assertEqual(cfg["governance"]["training_completion_rate"], 0.8)
        self.assertEqual(len(cfg["identity"]["accounts"]), 1)            # blank row dropped
        self.assertEqual(cfg["assets"][0]["public_ports"], [22, 3389])
        self.assertNotIn("max_critical_patch_age_days", cfg["assets"][0])  # empty cell left out
        result = assess(cfg)
        self.assertIn("IAM-01", {f.rule_id for f in result.findings})

    def test_bad_port_is_explained(self):
        from grc_assess.guided import build_config
        with self.assertRaises(ValueError):
            build_config({}, {}, assets=[{"hostname": "PC1", "public_ports": "RDP"}])


if __name__ == "__main__":
    unittest.main()
