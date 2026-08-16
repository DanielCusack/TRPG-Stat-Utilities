"""Populate the new recruitment_order and can_promote fields.

Characters were inserted by the scraper in recruitment order, so their primary
keys already encode it - except for variants added later (Sothe's Blossom
entries), which ended up at the very end of the list.
"""

from django.db import migrations

# Characters that never gain access to promotion despite their class having a
# promotion path.
NON_PROMOTABLE = ["Sothe"]


def base_name(name):
    """'Sothe (Fixed Blossom)' -> 'Sothe'."""
    return name.split("(")[0].strip()


def populate(apps, schema_editor):
    Character = apps.get_model("fe_data", "Character")

    characters = list(Character.objects.order_by("pk"))
    variants = [c for c in characters if "(" in c.name]
    originals = [c for c in characters if "(" not in c.name]

    # Rebuild the list so each variant sits immediately after the character it
    # varies, leaving every other character in its scraped position.
    ordered = []
    placed = set()
    for character in originals:
        ordered.append(character)
        placed.add(character.pk)
        for variant in variants:
            if variant.pk not in placed and base_name(variant.name) == character.name:
                ordered.append(variant)
                placed.add(variant.pk)

    # A variant whose base character is missing keeps its original position.
    ordered.extend(v for v in variants if v.pk not in placed)

    for position, character in enumerate(ordered):
        character.recruitment_order = position
        character.can_promote = base_name(character.name) not in NON_PROMOTABLE
        character.save(update_fields=["recruitment_order", "can_promote"])


def unpopulate(apps, schema_editor):
    Character = apps.get_model("fe_data", "Character")
    Character.objects.update(recruitment_order=0, can_promote=True)


class Migration(migrations.Migration):
    dependencies = [
        ("fe_data", "0005_alter_character_options_character_can_promote_and_more"),
    ]

    operations = [
        migrations.RunPython(populate, unpopulate),
    ]
