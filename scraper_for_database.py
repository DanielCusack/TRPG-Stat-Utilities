import requests
from fractions import Fraction
from bs4 import BeautifulSoup

from fe_data.models import FEClass, PromotionBonus, Character

class_name_mapping = {
    "Non-promoted physical": (
        "Ranger",
        "Myrmidon (M)",
        "Myrmidon (F)",
        "Soldier (F)",
        "Fighter",
        "Archer",
        "Knight",
        "Thief",
        "Pegasus Knight",
        "Sword Knight (M)",
        "Lance Knight (M)",
        "Bow Knight (M)",
        "Axe Knight (M)",
        "Wyvern Rider (M)",
        "Wyvern Rider (F)"

    ),
    "Horse Knight (F)": (
        "Bow Knight (F)",
    ),
    "Halberdier": (
        "Halberdier (F)",
        "Halberdier (M)",
    ),
    "Mage": (
        "Mage (F)",
        "Mage (M)",
    ),
    "Sage": (
        "Sage (F)",
        "Sage (M)",
    ),
    "Bishop": (
        "Bishop (M)",
    ),
}

female_mapping = (
    "Titania",
    "Mia",
    "Ilyana",
    "Lethe",
    "Nephenee",
    "Jill",
    "Astrid",
    "Calill",
    "Lucia",
    "Ena"
)  # Only including the ones that have an F suffix in their class

def parse_sothe_growth(growth: str):
    """Sothe's growths are displayed weirdly by serenes forest. Needs sanitisation"""
    if len(growth) > 3:
        return int(growth[:-3]) + Fraction(growth[-3:])
    return int(growth)


res_stats = requests.get("https://serenesforest.net/path-of-radiance/classes/maximum-stats/")
soup_stats = BeautifulSoup(res_stats.content, "html.parser")
stat_table = soup_stats.find("table")
stats_headers = ["hp", "strength", "magic", "skill", "speed", "luck", "defense", "resistance"]

fe_class_data = {}
for tr in stat_table.find_all("tr")[1:]:
    cells = [td.get_text(strip=True) for td in tr.find_all("td")]
    if cells:
        if cells[0].endswith("*"):
            continue
        names = cells[0].split("/")
        for name in names:
            stat_data = {}
            for stat_name, stat in zip(stats_headers, cells[1:]):
                stat_data[stat_name] = int(stat)
            fe_class_data[name.strip()] = stat_data

for generic_name, specific_names in class_name_mapping.items():
    class_data = fe_class_data.pop(generic_name)
    for specific_name in specific_names:
        fe_class_data[specific_name] = class_data.copy()

for class_name, max_stats in fe_class_data.items():
    FEClass.objects.create(
        name=class_name,
        promoted=(max_stats["hp"] > 40),
        **max_stats,
    )


res_gains = requests.get("https://serenesforest.net/path-of-radiance/classes/promotion-gains/")
soup_gains = BeautifulSoup(res_gains.content, "html.parser")
promotion_table = soup_gains.find("table")

for tr in promotion_table.find_all("tr")[1:]:
    cells = [td.get_text(strip=True).strip("+") for td in tr.find_all("td")]
    if cells:
        promo_from = FEClass.objects.filter(name=cells[0]).first()
        promo_to = FEClass.objects.filter(name=cells[1]).first()
        PromotionBonus.objects.create(
            from_class=promo_from,
            to_class=promo_to,
            hp=int(cells[2]),
            strength=int(cells[3]),
            magic=int(cells[4]),
            skill=int(cells[5]),
            speed=int(cells[6]),
            luck=0,
            defense=int(cells[7]),
            resistance=int(cells[8]),
        )

char_base = requests.get("https://serenesforest.net/path-of-radiance/characters/base-stats/")
soup_char_base = BeautifulSoup(char_base.content, "html.parser")
gains_table = soup_char_base.find("table")

characters= {}
for tr in gains_table.find_all("tr")[1:]:
    cells = [td.get_text(strip=True).strip("+") for td in tr.find_all("td")]
    if not cells:
        continue

    fe_class = FEClass.objects.filter(name=cells[1]).first()
    if not fe_class:
        if cells[0] in female_mapping:
            if "tribe" in cells[1]:
                fe_class = FEClass.objects.filter(name=cells[1][:-1] + " F)").first()
            else:
                fe_class = FEClass.objects.filter(name=cells[1] + " (F)").first()
        else:
            if "tribe" in cells[1]:
                fe_class = FEClass.objects.filter(name=cells[1][:-1] + " M)").first()
            else:
                fe_class = FEClass.objects.filter(name=cells[1] + " (M)").first()
    if not fe_class:
        raise RuntimeError(
            f"Unable to resolve class ({cells[1]}) for {cells[0]} "
        )
        
    characters[cells[0]] = {
        "base_class": fe_class,
        "base_level": cells[2],
        "base_hp": cells[3],
        "base_strength": cells[4],
        "base_magic": cells[5],
        "base_skill": cells[6],
        "base_speed": cells[7],
        "base_luck": cells[8],
        "base_defense": cells[9],
        "base_resistance": cells[10],
    }

char_growths = requests.get("https://serenesforest.net/path-of-radiance/characters/growth-rates/")
soup_char_growths = BeautifulSoup(char_growths.content, "html.parser")

for tr in soup_char_growths.find_all("tr")[1:]:
    cells = [td.get_text(strip=True) for td in tr.find_all("td")]
    if not cells:
        continue
    try:
        characters[cells[0]].update(
            {
                "growth_hp": cells[1],
                "growth_strength": cells[2],
                "growth_magic": cells[3],
                "growth_skill": cells[4],
                "growth_speed": cells[5],
                "growth_luck": cells[6],
                "growth_defense": cells[7],
                "growth_resistance": cells[8],
            }
        )
    except KeyError:
        assert "Sothe" in cells[0], f"non Sothe character is having issues {cells[0]}"
        if "1" in cells[0]:
            sothe_name = "Sothe (Fixed Blossom)"
            characters[sothe_name] = characters["Sothe"].copy()
        else:
            sothe_name = "Sothe (Random Blossom)"
            characters[sothe_name] = characters["Sothe"].copy()
        characters[sothe_name].update(
            {
                "growth_hp": parse_sothe_growth(cells[1]),
                "growth_strength": parse_sothe_growth(cells[2]),
                "growth_magic": parse_sothe_growth(cells[3]),
                "growth_skill": parse_sothe_growth(cells[4]),
                "growth_speed": parse_sothe_growth(cells[5]),
                "growth_luck": parse_sothe_growth(cells[6]),
                "growth_defense": parse_sothe_growth(cells[7]),
                "growth_resistance": parse_sothe_growth(cells[8]),
            }
        )

for name, info in characters.items():
    Character.objects.create(
        name=name,
        **info,
    )
