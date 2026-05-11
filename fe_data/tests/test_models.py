from django.test import TestCase
from pytest import approx
from fe_data.models import Character, FEClass, PromotionBonus


class CharacterMethodTestCase(TestCase):
    def setUp(self):
        unpromotable_class = FEClass.objects.create(
            name="unpromotable class",
            hp=100,
            strength=100,
            magic=100,
            skill=100,
            speed=100,
            luck=100,
            defense=100,
            resistance=100,
        )
        unpromoted_class = FEClass.objects.create(
            name="unpromoted class",
            hp=20,
            strength=20,
            magic=20,
            skill=20,
            speed=20,
            luck=20,
            defense=20,
            resistance=20,
        )
        promoted_class = FEClass.objects.create(
            name="promoted class",
            hp=40,
            strength=40,
            magic=40,
            skill=40,
            speed=40,
            luck=40,
            defense=40,
            resistance=50,
        )
        PromotionBonus.objects.create(
            from_class=unpromoted_class,
            to_class=promoted_class,
            hp=5,
            strength=5,
            magic=5,
            skill=5,
            speed=5,
            luck=0,
            defense=5,
            resistance=5,
        )

        Character.objects.create(
            name="test no promo",
            base_class=unpromotable_class,
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

        Character.objects.create(
            name="test no promo near cap",
            base_class=unpromotable_class,
            base_level=1,
            base_hp=1,
            base_strength=1,
            base_magic=1,
            base_skill=1,
            base_speed=99,
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

        Character.objects.create(
            name="test promo",
            base_class=unpromoted_class,
            base_level=15,
            base_hp=15,
            base_strength=20,
            base_magic=10,
            base_skill=17,
            base_speed=17,
            base_luck=17,
            base_defense=13,
            base_resistance=12,
            growth_hp=60,
            growth_strength=60,
            growth_magic=60,
            growth_skill=60,
            growth_speed=60,
            growth_luck=60,
            growth_defense=140,
            growth_resistance=160,
        )

    def test_percentile_calculation_no_promo(self):
        """test that the percentile calculation works for the
        simplist case where the character does not promote and
        the stats given are valid"""
        valid_stats = {
            "hp": 8,
            "strength": 2,
            "magic": 1,  # No stat ups
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
            "magic": 1,
            "skill": 0.9744,
            "speed": 0.4752,
            "luck": 1.0,
            "defense": 0.31640625,
            "resistance": 0.0001,
        }
        assert actual_percentiles == approx(
            expected_percentiles
        ), f"actual percentiles are different from expected\nActual: {actual_percentiles}\nExpect: {expected_percentiles}"

    def test_percentile_calculation_no_promo_non_valid(self):
        """test that the percentile calculation works for the
        case where the character does not promote and the stats
        are not valid"""
        valid_stats = {
            "hp": 10,  # Too high
            "strength": 10,
            "magic": 10,
            "skill": 10,
            "speed": 101,  # Above cap but reachable otherwise
            "luck": 1000,  # Above cap and not reachable
            "defense": 0,  # Below cap
            "resistance": 0,
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
            "hp": 0,
            "strength": 0,
            "magic": 0,
            "skill": 0,
            "speed": 0,
            "luck": 0,
            "defense": 1,
            "resistance": 1,
        }
        assert actual_percentiles == approx(
            expected_percentiles
        ), f"actual percentiles are different from expected\nActual: {actual_percentiles}\nExpect: {expected_percentiles}"

    def test_percentile_calculation_promo(self):
        """test that the percentile calculation works for the
        case where the character can promote and
        the stats given are valid.
        """
        valid_stats = {
            "hp": 25,  # Edgecase as there are 5 levels unpromoted
            "strength": 25,  # No stat ups starting at max in unpromo class
            "magic": 15,  # No stat ups not starting at max in unpromo
            "skill": 30,  # Probably the most typical case
            "speed": 34,  # Max possible value considering unpromo cap
            "luck": 25,  # Same as skill but with a promo bonus of 0
            "defense": 42,  # Typical case for >100% growth
            "resistance": 43,  # Max possible value considering unpromo cap >100% growth
        }
        level = 10  # 9 level ups
        character = Character.objects.get(
            name="test promo",
        )
        actual_percentiles = character.calculate_stat_percentiles(
            stats=valid_stats,
            level=level,
            promoted=True,
        )
        expected_percentiles = {
            "hp": 0.9824904585216,
            "strength": 1,
            "magic": 1,
            "skill": 0.6303284424,  # Not 0.692452...
            "speed": 0.006878632182,  # Not 0.03979158...
            "luck": 0.6303284424,  # Not 0.692452...
            "defense": 0.0025882211123,  # Not 0.0175095...
            "resistance": 0.006878632182,  # Not 0.03979158...
        }
        assert actual_percentiles == approx(
            expected_percentiles
        ), f"actual percentiles are different from expected\nActual: {actual_percentiles}\nExpect: {expected_percentiles}"
