from django.test import TestCase

from fe_data.constants import FE_STAT_NAMES
from fe_data.models import Character, FEClass


class CharacterOrderingTestCase(TestCase):
    """Characters are listed in recruitment order, which the dropdown and the
    API both rely on. Without explicit ordering the database is free to return
    rows in any order."""

    def setUp(self):
        self.fe_class = FEClass.objects.create(
            name="Test Class",
            promoted=False,
            level_cap=20,
            **{stat: 99 for stat in FE_STAT_NAMES},
        )
        self.stats = {
            **{f"base_{stat}": 5 for stat in FE_STAT_NAMES},
            **{f"growth_{stat}": 50 for stat in FE_STAT_NAMES},
        }

    def create(self, name, recruitment_order):
        return Character.objects.create(
            name=name,
            base_class=self.fe_class,
            base_level=1,
            recruitment_order=recruitment_order,
            **self.stats,
        )

    def test_characters_are_returned_in_recruitment_order(self):
        # Created out of order on purpose.
        self.create("Third", 2)
        self.create("First", 0)
        self.create("Second", 1)

        self.assertEqual(
            list(Character.objects.values_list("name", flat=True)),
            ["First", "Second", "Third"],
        )

    def test_ordering_is_independent_of_insertion_order(self):
        """A character added later still sorts into its recruitment slot,
        which is the bug that left the Sothe variants at the bottom."""
        self.create("Early", 0)
        self.create("Late", 2)
        self.create("Inserted Afterwards", 1)

        self.assertEqual(
            list(Character.objects.values_list("name", flat=True)),
            ["Early", "Inserted Afterwards", "Late"],
        )
