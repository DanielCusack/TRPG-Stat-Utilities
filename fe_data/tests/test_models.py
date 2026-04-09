from django.test import TestCase
from pytest import approx
from fe_data.models import Character, FEClass


class CharacterMethodTestCase(TestCase):
    def setUp(self):
        unpromoted_class = FEClass.objects.create(
            name="unpromoted class",
            hp=100,
            strength=100,
            magic=100,
            skill=100,
            speed=100,
            luck=100,
            defense=100,
            resistance=100,
        )
        Character.objects.create(
            name="test no promo",
            base_class=unpromoted_class,
            base_level=1,
            base_hp=1,
            base_strength=1,
            base_magic=1,
            base_skill=1,
            base_speed=1,
            base_luck=1,
            base_defense=1,
            base_resistance=1,
            growth_hp=150,  # Growths can be > 100%
            growth_strength=50,
            growth_magic=60,
            growth_skill=60,
            growth_speed=60,
            growth_luck=60,
            growth_defense=75,
            growth_resistance=10,
        )

    def test_percentile_calculation_no_promo(self):
        """test that the percentile calculation works for the
        simplist case where the character does not promote and
        the stats given are valid"""
        valid_stats = {
            "hp": 8,
            "strength": 2,
            "magic": 3,
            "skill": 2,
            "speed": 4,
            "luck": 1,
            "defense": 5,
            "resistance": 5,  # Very low chance!
        }
        level = 5  # 4 level ups
        character = Character.objects.get(
            name="test no promo",
        )
        actual_percentiles = character.calculate_stat_percentiles(
            stats=valid_stats,
            level=level,
            promoted=False,
        )
        expected_percentiles = {
            "hp": 0.3125,
            "strength": 0.9375,
            "magic": 0.8208,
            "skill": 0.9744,
            "speed": 0.4752,
            "luck": 1.0,
            "defense": 0.31640625,
            "resistance": 0.0001,
        }
        assert actual_percentiles == approx(
            expected_percentiles
        ), f"actual percentiles are different from expected\nActual: {actual_percentiles}\nExpect: {expected_percentiles}"
