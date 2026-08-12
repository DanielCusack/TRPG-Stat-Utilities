from django.test import TestCase
from django.urls import reverse

from fe_data.constants import FE_STAT_NAMES
from fe_data.models import Character, FEClass


class StatCheckViewTestCase(TestCase):
    def setUp(self):
        self.url = reverse("calculator:stat-check")

        self.unpromoted_class = FEClass.objects.create(
            name="Unpromoted Class",
            promoted=False,
            level_cap=20,
            hp=99,
            strength=99,
            magic=99,
            skill=99,
            speed=99,
            luck=99,
            defense=99,
            resistance=99,
        )
        self.promoted_class = FEClass.objects.create(
            name="Promoted Class",
            promoted=True,
            level_cap=20,
            hp=99,
            strength=99,
            magic=99,
            skill=99,
            speed=99,
            luck=99,
            defense=99,
            resistance=99,
        )

        # Base 5 / growth 50% in every stat keeps the expected-value and
        # percentile maths simple enough to verify by hand.
        self.unpromoted_character = Character.objects.create(
            name="Unpromoted Hero",
            base_class=self.unpromoted_class,
            base_level=1,
            **{f"base_{stat}": 5 for stat in FE_STAT_NAMES},
            **{f"growth_{stat}": 50 for stat in FE_STAT_NAMES},
        )
        self.promoted_character = Character.objects.create(
            name="Promoted Hero",
            base_class=self.promoted_class,
            base_level=10,
            **{f"base_{stat}": 5 for stat in FE_STAT_NAMES},
            **{f"growth_{stat}": 50 for stat in FE_STAT_NAMES},
        )

    def post_data(self, character, level, stat_value, promoted=None):
        data = {
            "character": character.pk,
            "level": level,
            **{stat: stat_value for stat in FE_STAT_NAMES},
        }
        if promoted:
            data["promoted"] = "on"
        return data

    def test_get_renders_blank_form_with_no_results(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "calculator/stat_check.html")
        self.assertIsNone(response.context["results"])
        self.assertFalse(response.context["form"].is_bound)

    def test_character_data_context_covers_every_character(self):
        response = self.client.get(self.url)
        character_data = response.context["character_data"]

        self.assertEqual(
            set(character_data),
            {self.unpromoted_character.pk, self.promoted_character.pk},
        )

        unpromoted = character_data[self.unpromoted_character.pk]
        self.assertEqual(unpromoted["base"], {stat: 5 for stat in FE_STAT_NAMES})
        self.assertEqual(unpromoted["growth"], {stat: 50 for stat in FE_STAT_NAMES})
        self.assertFalse(unpromoted["promoted"])

        self.assertTrue(character_data[self.promoted_character.pk]["promoted"])

    def test_valid_post_assembles_results_for_every_stat(self):
        """Base 5, growth 50%, level 1 -> 5 is 4 level ups, so the expected
        value is 5 + 4 * 0.5 = 7.0. An actual stat of 7 therefore has a
        difference of 0.0, and needs at least 2 stat ups in 4 level ups at
        p=0.5, i.e. (6 + 4 + 1) / 16 = 0.6875 -> 68.75%.
        """
        response = self.client.post(
            self.url,
            self.post_data(self.unpromoted_character, level=5, stat_value=7),
        )

        self.assertEqual(response.status_code, 200)
        results = response.context["results"]
        self.assertEqual(set(results), set(FE_STAT_NAMES))
        for stat in FE_STAT_NAMES:
            self.assertEqual(
                results[stat],
                {
                    "actual": 7,
                    "expected": 7.0,
                    "difference": 0.0,
                    "percentile": 68.75,
                },
                f"unexpected results for {stat}",
            )

    def test_valid_post_reports_difference_against_expected(self):
        """Same fixture as above, but an actual stat of 9 is 2 above the
        expected 7.0, and needs at least 4 stat ups in 4 level ups at
        p=0.5, i.e. 1 / 16 = 0.0625 -> 6.25%.
        """
        response = self.client.post(
            self.url,
            self.post_data(self.unpromoted_character, level=5, stat_value=9),
        )

        self.assertEqual(
            response.context["results"]["hp"],
            {
                "actual": 9,
                "expected": 7.0,
                "difference": 2.0,
                "percentile": 6.25,
            },
        )

    def test_valid_post_redisplays_bound_form_with_submitted_values(self):
        response = self.client.post(
            self.url,
            self.post_data(self.unpromoted_character, level=5, stat_value=7),
        )

        form = response.context["form"]
        self.assertTrue(form.is_bound)
        self.assertFalse(form.errors)
        self.assertEqual(form.cleaned_data["character"], self.unpromoted_character)
        self.assertEqual(form.cleaned_data["level"], 5)

    def test_valid_post_for_character_starting_promoted_still_forces_promoted(self):
        """The view no longer rebuilds the form to show the forced promotion —
        the template's JS checks and disables the checkbox for a character that
        starts promoted. clean() still forces promoted=True for the calculation.
        """
        response = self.client.post(
            self.url,
            self.post_data(self.promoted_character, level=10, stat_value=5),
        )

        self.assertTrue(response.context["form"].cleaned_data["promoted"])

    def test_invalid_post_returns_bound_form_with_errors_and_no_results(self):
        response = self.client.post(
            self.url,
            self.post_data(self.promoted_character, level=9, stat_value=5),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["results"])
        form = response.context["form"]
        self.assertTrue(form.is_bound)
        self.assertIn("level", form.errors)

    def test_post_without_character_returns_form_errors_and_no_results(self):
        data = self.post_data(self.unpromoted_character, level=5, stat_value=7)
        del data["character"]

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["results"])
        self.assertIn("character", response.context["form"].errors)
