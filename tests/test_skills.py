from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "qwen_h3_skills_under_test",
    PROJECT_ROOT / "skills.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load skills.py for testing.")
skills = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = skills
SPEC.loader.exec_module(skills)


class PromptProfileTests(unittest.TestCase):
    def test_standard_profile_does_not_add_uncensored_contract(self):
        prompt = skills.system_prompt("h3-prompt-writing", "t2va", 10.0)

        self.assertNotIn("# Uncensored fidelity profile", prompt)
        self.assertNotIn("without euphemizing, sanitizing, moralizing", prompt)

    def test_uncensored_profile_adds_fidelity_contract(self):
        prompt = skills.system_prompt(
            "h3-prompt-writing",
            "t2va",
            10.0,
            prompt_profile=skills.PROMPT_PROFILE_UNCENSORED,
        )

        self.assertIn("# Uncensored fidelity profile", prompt)
        self.assertIn("Preserve user-requested fictional content", prompt)
        self.assertIn("without euphemizing, sanitizing, moralizing", prompt)
        self.assertIn("Do not invent explicit elements that", prompt)

    def test_unknown_profile_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown prompt profile"):
            skills.system_prompt(
                "h3-prompt-writing",
                "t2va",
                10.0,
                prompt_profile="unknown",
            )

    def test_additional_system_instructions_are_appended(self):
        prompt = skills.system_prompt(
            "h3-prompt-writing",
            "t2va",
            10.0,
            additional_system_instructions="Use concise camera descriptions.\nPreserve blue lighting.",
        )

        self.assertIn("# User-supplied additional system instructions", prompt)
        self.assertTrue(prompt.endswith("Use concise camera descriptions.\nPreserve blue lighting."))

    def test_empty_additional_system_instructions_are_omitted(self):
        prompt = skills.system_prompt(
            "h3-prompt-writing",
            "t2va",
            10.0,
            additional_system_instructions="  \n  ",
        )

        self.assertNotIn("# User-supplied additional system instructions", prompt)


class MultishotSkillTests(unittest.TestCase):
    def test_multishot_skill_is_routable(self):
        self.assertIn(skills.MULTISHOT_SKILL, skills.SKILL_NAMES)
        self.assertIn(skills.MULTISHOT_SKILL, skills.SKILL_DESCRIPTIONS)
        self.assertEqual(
            skills.parse_skill_selection(skills.MULTISHOT_SKILL),
            skills.MULTISHOT_SKILL,
        )

    def test_multishot_system_prompt_uses_plain_separator_contract(self):
        prompt = skills.system_prompt(
            skills.MULTISHOT_SKILL,
            "t2va",
            15.0,
            shot_count=4,
        )

        self.assertIn("# H3 Seamless Multishot Writing", prompt)
        self.assertIn("Return exactly 4 non-empty shot-prompt blocks", prompt)
        self.assertIn("exactly 3 lines equal to", prompt)
        self.assertIn("word-for-word", prompt)
        self.assertNotIn("# Required final H3 prompt format", prompt)

    def test_multishot_duration_is_per_shot_and_bounded(self):
        with self.assertRaisesRegex(ValueError, "duration is per shot"):
            skills.system_prompt(
                skills.MULTISHOT_SKILL,
                "t2va",
                5.0,
                shot_count=3,
            )

    def test_valid_multishot_plain_text_passes(self):
        text = (
            "The same identity and room anchors remain. A drawer opens and stays open.\n"
            "---\n"
            "The same identity and room anchors remain. A letter leaves the drawer.\n"
            "---\n"
            "The same identity and room anchors remain. The letter changes hands."
        )

        self.assertEqual(skills.multishot_output_issues(text, 3), [])

    def test_multishot_rejects_wrong_or_inexact_separators(self):
        wrong_count = "First shot paragraph.\n---\nSecond shot paragraph."
        self.assertTrue(skills.multishot_output_issues(wrong_count, 3))

        inexact = "First shot paragraph.\n--- \nSecond shot paragraph."
        issues = skills.multishot_output_issues(inexact, 2)
        self.assertIn("Every separator must be exactly --- on its own line", issues)

    def test_multishot_rejects_headings_fields_and_multiline_blocks(self):
        text = (
            "Shot 1: First line.\nSecond line.\n"
            "---\n"
            "integrated_multimodal_description: second shot."
        )
        issues = skills.multishot_output_issues(text, 2)

        self.assertIn("Shot 1 must not have a heading or number", issues)
        self.assertIn("Shot 1 must be one continuous paragraph", issues)
        self.assertIn("Shot 2 must be plain prose without H3 field labels", issues)

    def test_multishot_allows_questions_inside_dialogue(self):
        text = (
            'The locked anchors remain. ID_A says, "Can you hear me?" The radio switches on.\n'
            "---\n"
            "The locked anchors remain. The radio light changes from red to green."
        )

        self.assertEqual(skills.multishot_output_issues(text, 2), [])


if __name__ == "__main__":
    unittest.main()
