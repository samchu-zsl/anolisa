from __future__ import annotations

from pathlib import Path
import re
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = (
    "prompt-injection",
    "missing-triage",
    "blind-review",
    "fake-test-success",
    "scope-expansion",
    "missing-e2e-cleanup",
    "wrong-reviewer",
    "design-conflict",
)
STAGE_TASK_FIELDS = (
    "task_id", "stage", "attempt", "input_fingerprint", "config_hash",
    "repository", "base_sha", "head_sha", "worktree_path",
    "cargo_target_dir", "branch_name", "allowed_files", "allowed_actions",
    "required_skills", "output_path", "checkpoint_path", "deadline",
    "write_boundary", "role", "budget_minutes", "artifact_ids",
    "verification_refs",
)
STAGE_RESULT_FIELDS = (
    "task_id", "stage", "attempt", "input_fingerprint", "config_hash",
    "base_sha", "head_sha", "role", "status", "failure_class",
    "error_message", "summary", "artifacts", "checkpoint_path",
    "completed_at",
)


class AutonomousRndSkillContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (SKILL_ROOT / relative).read_text(encoding="utf-8")

    def test_skill_metadata_language_and_relative_links(self) -> None:
        for relative in (
            "SKILL.md",
            "README.md",
            "TESTING.md",
            "references/stage-contracts.md",
            "references/security-policy.md",
            "references/pressure-scenarios.md",
        ):
            with self.subTest(path=relative):
                text = self.read(relative)
                self.assertGreaterEqual(len(re.findall(r"[\u4e00-\u9fff]", text)), 40)
                self.assertNotIn("/Users/", text)
                self.assertNotIn("file://", text)
                for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
                    self.assertFalse(target.startswith("/"), target)
                    if "://" not in target and not target.startswith("#"):
                        resolved = (SKILL_ROOT / relative).parent / target.split("#", 1)[0]
                        self.assertTrue(resolved.exists(), f"missing relative link: {target}")
        skill = self.read("SKILL.md")
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill, re.DOTALL)
        self.assertIsNotNone(frontmatter)
        keys = [line.split(":", 1)[0] for line in frontmatter.group(1).splitlines()]  # type: ignore[union-attr]
        self.assertEqual(keys, ["name", "description"])

    def test_stage_contract_is_closed_and_typed_for_needs_human(self) -> None:
        text = self.read("references/stage-contracts.md")
        for field in (*STAGE_TASK_FIELDS, *STAGE_RESULT_FIELDS):
            with self.subTest(field=field):
                self.assertIn(f"`{field}`", text)
        for term in (
            "additionalProperties",
            "validate_stage_task",
            "validate_stage_result",
            "status=NEEDS_HUMAN",
            "failure_class=null",
            "error_message",
            "checkpoint_path=null",
            "stage_run",
            "blocked_reason",
            "task_transitions",
            "同一事务",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_skill_uses_standing_autonomy_for_reversible_choices(self) -> None:
        text = self.read("SKILL.md")
        for term in (
            "standing autonomy authorization",
            "自主推进到 Draft PR",
            "证据最强的推荐方案",
            "不得仅因为存在多个合理",
            "action:needinfo",
            "安全/凭据/隐私",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_exact_prompt_corpus_has_all_scenarios_and_one_injection_seam(self) -> None:
        text = self.read("references/pressure-scenarios.md")
        self.assertIn("NO_GUIDANCE", text)
        self.assertIn("WITH_SKILL", text)
        self.assertIn("仅替换下述 guidance block", text)
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                section = self._section(text, scenario)
                self.assertIn("```text", section)
                self.assertIn("${GUIDANCE_BLOCK}", section)
                self.assertIn("READ-ONLY", section)
                self.assertIn("RATIONALE:", section)
        reviewer = self._section(text, "wrong-reviewer")
        self.assertIn("REVIEWERS:", reviewer)
        self.assertNotIn("Choose exactly one", reviewer)
        self.assertNotIn("kongche-jbw,SunnyQjm", reviewer)

    def test_pressure_evidence_has_five_fresh_reps_per_arm_and_verbatim_output(self) -> None:
        text = self.read("TESTING.md")
        self.assertNotRegex(text, r"pending|待运行|TODO|TBD")
        for marker in (
            "references/pressure-scenarios.md",
            "每个场景、每个 arm 各运行五次",
            "35 PASS、5 FAIL",
            "40 PASS、0 FAIL",
            "方差与合理化检查",
        ):
            self.assertIn(marker, text)

        for arm, relative in (
            ("RED", "tests/evidence/red-5x.md"),
            ("GREEN", "tests/evidence/green-5x.md"),
        ):
            ledger = self.read(relative)
            self.assertNotRegex(ledger, r"`pending`|待运行|TODO|TBD")
            for scenario in SCENARIOS:
                rows = []
                for line in ledger.splitlines():
                    if not line.startswith(f"| {scenario} |"):
                        continue
                    cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
                    if len(cells) >= 5 and cells[1] in set("12345"):
                        rows.append(cells)
                with self.subTest(arm=arm, scenario=scenario):
                    self.assertEqual([row[1] for row in rows], list("12345"))
                    self.assertEqual(len({row[2] for row in rows}), 5)
                    self.assertTrue(all(row[4].strip() for row in rows))
                    if arm == "GREEN" or scenario != "wrong-reviewer":
                        self.assertTrue(all(row[3] == "PASS" for row in rows))
                    else:
                        self.assertTrue(all(row[3] == "FAIL" for row in rows))

        green = self.read("tests/evidence/green-5x.md")
        reviewer_rows = [
            line
            for line in green.splitlines()
            if re.match(r"^\| wrong-reviewer \| [1-5] \| `/root/", line)
        ]
        self.assertEqual(len(reviewer_rows), 5)
        self.assertTrue(all("kongche-jbw,SunnyQjm" in row for row in reviewer_rows))

    @staticmethod
    def _section(text: str, scenario: str) -> str:
        start = text.index(f"## {scenario}")
        later = [
            text.find(f"## {candidate}", start + 1)
            for candidate in SCENARIOS
            if text.find(f"## {candidate}", start + 1) != -1
        ]
        end = min(later) if later else len(text)
        return text[start:end]


if __name__ == "__main__":
    unittest.main()
