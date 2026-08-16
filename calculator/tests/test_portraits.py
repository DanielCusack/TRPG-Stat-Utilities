from django.test import TestCase
from django.urls import reverse

from calculator.portraits import (
    available_portraits,
    default_portrait_path,
    portrait_path,
    portrait_slug,
)
from fe_data.constants import FE_STAT_NAMES
from fe_data.models import Character, FEClass


class PortraitSlugTests(TestCase):
    def test_plain_name_is_lowercased(self):
        self.assertEqual(portrait_slug("Ike"), "ike")

    def test_sothe_variants_share_one_slug(self):
        slugs = {
            portrait_slug("Sothe"),
            portrait_slug("Sothe (Fixed Blossom)"),
            portrait_slug("Sothe (Random Blossom)"),
        }
        self.assertEqual(slugs, {"sothe"})


class PortraitPathTests(TestCase):
    def test_known_character_uses_own_portrait(self):
        self.assertEqual(
            portrait_path("Ike", {"ike.png", "default.png"}),
            "calculator/portraits/ike.png",
        )

    def test_character_without_portrait_falls_back_to_default(self):
        self.assertEqual(
            portrait_path("Titania", {"ike.png", "default.png"}),
            default_portrait_path(),
        )

    def test_sothe_variants_all_resolve_to_sothe(self):
        available = {"sothe.png", "default.png"}
        for name in ("Sothe", "Sothe (Fixed Blossom)", "Sothe (Random Blossom)"):
            with self.subTest(name=name):
                self.assertEqual(
                    portrait_path(name, available), "calculator/portraits/sothe.png"
                )

    def test_shipped_assets_are_discoverable(self):
        """Guards the directory location: if the portraits move, the fallback
        would silently apply to every character instead of erroring."""
        available = available_portraits()
        self.assertIn("default.png", available)
        self.assertIn("ike.png", available)


class PortraitViewContextTests(TestCase):
    def setUp(self):
        self.url = reverse("calculator:stat-check")
        fe_class = FEClass.objects.create(
            name="Test Class",
            promoted=False,
            level_cap=20,
            **{stat: 99 for stat in FE_STAT_NAMES},
        )
        stats = {
            **{f"base_{stat}": 5 for stat in FE_STAT_NAMES},
            **{f"growth_{stat}": 50 for stat in FE_STAT_NAMES},
        }
        # "Ike" has a portrait file; the others deliberately do not.
        self.ike = Character.objects.create(
            name="Ike", base_class=fe_class, base_level=1, **stats
        )
        self.sothe = Character.objects.create(
            name="Sothe", base_class=fe_class, base_level=1, **stats
        )
        self.sothe_blossom = Character.objects.create(
            name="Sothe (Fixed Blossom)", base_class=fe_class, base_level=1, **stats
        )
        self.no_portrait = Character.objects.create(
            name="Nobody", base_class=fe_class, base_level=1, **stats
        )

    def test_every_character_has_a_portrait_url(self):
        response = self.client.get(self.url)
        character_data = response.context["character_data"]

        self.assertTrue(all("portrait" in entry for entry in character_data.values()))

    def test_character_with_portrait_gets_own_image(self):
        response = self.client.get(self.url)
        portrait = response.context["character_data"][self.ike.pk]["portrait"]

        self.assertTrue(portrait.endswith("ike.png"), portrait)

    def test_sothe_variants_share_the_same_portrait(self):
        response = self.client.get(self.url)
        character_data = response.context["character_data"]

        self.assertEqual(
            character_data[self.sothe.pk]["portrait"],
            character_data[self.sothe_blossom.pk]["portrait"],
        )

    def test_character_without_portrait_gets_default(self):
        response = self.client.get(self.url)
        character_data = response.context["character_data"]

        self.assertEqual(
            character_data[self.no_portrait.pk]["portrait"],
            response.context["default_portrait"],
        )

    def test_default_portrait_is_rendered_for_no_selection(self):
        response = self.client.get(self.url)

        self.assertContains(response, response.context["default_portrait"])
