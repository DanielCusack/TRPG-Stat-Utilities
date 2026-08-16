from django.test import TestCase

from calculator.forms import StatCheckForm
from fe_data.constants import FE_STAT_NAMES
from fe_data.models import Character, FEClass


class StatCheckFormTestCase(TestCase):
    def setUp(self):
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
        self.unpromoted_character = Character.objects.create(
            name="Unpromoted Hero",
            base_class=self.unpromoted_class,
            base_level=5,
            base_hp=1,
            base_strength=1,
            base_magic=1,
            base_skill=1,
            base_speed=1,
            base_luck=1,
            base_defense=1,
            base_resistance=1,
            growth_hp=50,
            growth_strength=50,
            growth_magic=50,
            growth_skill=50,
            growth_speed=50,
            growth_luck=50,
            growth_defense=50,
            growth_resistance=50,
        )
        self.promoted_character = Character.objects.create(
            name="Promoted Hero",
            base_class=self.promoted_class,
            base_level=10,
            base_hp=1,
            base_strength=1,
            base_magic=1,
            base_skill=1,
            base_speed=1,
            base_luck=1,
            base_defense=1,
            base_resistance=1,
            growth_hp=50,
            growth_strength=50,
            growth_magic=50,
            growth_skill=50,
            growth_speed=50,
            growth_luck=50,
            growth_defense=50,
            growth_resistance=50,
        )
        # Same unpromoted class as above, but this character never gains access
        # to promotion (Sothe's situation: a Thief who cannot become an
        # Assassin, unlike Volke).
        self.non_promotable_character = Character.objects.create(
            name="Cannot Promote",
            base_class=self.unpromoted_class,
            base_level=1,
            can_promote=False,
            **{f"base_{stat}": 5 for stat in FE_STAT_NAMES},
            **{f"growth_{stat}": 50 for stat in FE_STAT_NAMES},
        )
        self.stat_fields = {
            "hp": 10,
            "strength": 10,
            "magic": 10,
            "skill": 10,
            "speed": 10,
            "luck": 10,
            "defense": 10,
            "resistance": 10,
        }

    def test_unpromoted_character_at_base_level_is_valid(self):
        data = {
            "character": self.unpromoted_character.pk,
            "level": self.unpromoted_character.base_level,
            **self.stat_fields,
        }
        form = StatCheckForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data["promoted"])

    def test_unpromoted_character_with_promoted_checkbox_checked_is_valid(self):
        data = {
            "character": self.unpromoted_character.pk,
            "level": self.unpromoted_character.base_level,
            "promoted": "on",
            **self.stat_fields,
        }
        form = StatCheckForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data["promoted"])

    def test_character_that_starts_promoted_forces_promoted_true(self):
        data = {
            "character": self.promoted_character.pk,
            "level": self.promoted_character.base_level,
            **self.stat_fields,
        }
        form = StatCheckForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data["promoted"])

    def test_character_that_starts_promoted_below_base_level_is_invalid(self):
        data = {
            "character": self.promoted_character.pk,
            "level": self.promoted_character.base_level - 1,
            **self.stat_fields,
        }
        form = StatCheckForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["level"],
            [
                f"{self.promoted_character.name} must be at least level "
                f"{self.promoted_character.base_level}."
            ],
        )

    def test_unpromoted_character_below_base_level_with_checkbox_unchecked_is_invalid(
        self,
    ):
        data = {
            "character": self.unpromoted_character.pk,
            "level": self.unpromoted_character.base_level - 1,
            **self.stat_fields,
        }
        form = StatCheckForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["level"],
            [
                f"An unpromoted {self.unpromoted_character.name} must be at "
                f"least level {self.unpromoted_character.base_level}"
            ],
        )

    def test_unpromoted_character_below_base_level_with_checkbox_checked_is_valid(
        self,
    ):
        """Documents current behaviour: checking "promoted" bypasses the
        below-base-level check for a character that starts unpromoted, since
        clean() only runs that check when cleaned_data["promoted"] is False.
        """
        data = {
            "character": self.unpromoted_character.pk,
            "level": self.unpromoted_character.base_level - 1,
            "promoted": "on",
            **self.stat_fields,
        }
        form = StatCheckForm(data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_non_promotable_character_rejects_promotion(self):
        """The UI disables the checkbox, but that is not a guarantee - a
        crafted request must still be rejected server side."""
        data = {
            "character": self.non_promotable_character.pk,
            "level": 5,
            "promoted": "on",
            **self.stat_fields,
        }
        form = StatCheckForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["promoted"],
            [f"{self.non_promotable_character.name} cannot promote."],
        )

    def test_non_promotable_character_is_valid_when_unpromoted(self):
        data = {
            "character": self.non_promotable_character.pk,
            "level": 5,
            **self.stat_fields,
        }
        form = StatCheckForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data["promoted"])

    def test_missing_character_is_invalid_without_crashing(self):
        """clean() skips the cross-field checks when no character was
        selected, rather than crashing on `character.base_class`.
        """
        data = {"level": 5, **self.stat_fields}
        form = StatCheckForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("character", form.errors)

    def test_level_outside_min_max_range_is_invalid_without_crashing(self):
        """clean() skips the cross-field checks when level fails its own
        min/max validation, rather than crashing on `level < base_level`.
        """
        data = {
            "character": self.unpromoted_character.pk,
            "level": 0,
            **self.stat_fields,
        }
        form = StatCheckForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("level", form.errors)
