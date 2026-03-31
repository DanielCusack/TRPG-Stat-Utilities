from django.shortcuts import render
from .forms import StatCheckForm
from fe_data.models import PromotionBonus
from .utils import calculate_promoted_stat, classify_stat, expected_stat

def stat_check_view(request):
    results = None

    if request.method == "POST":
        form = StatCheckForm(request.POST)
        if form.is_valid():
            # Form clean can change the promoted value thus the display may need updating
            display_form = StatCheckForm(initial=form.cleaned_data)
            character = form.cleaned_data["character"]
            level = form.cleaned_data["level"]

            actual_stats = {
                "hp": form.cleaned_data["hp"],
                "strength": form.cleaned_data["strength"],
                "magic": form.cleaned_data["magic"],
                "skill": form.cleaned_data["skill"],
                "speed": form.cleaned_data["speed"],
                "luck": form.cleaned_data["luck"],
                "defense": form.cleaned_data["defense"],
                "resistance": form.cleaned_data["resistance"],
            }

            base_stats = {
                "hp": character.base_hp,
                "strength": character.base_strength,
                "magic": character.base_magic,
                "skill": character.base_skill,
                "speed": character.base_speed,
                "luck": character.base_luck,
                "defense": character.base_defense,
                "resistance": character.base_resistance,
            }

            growths = {
                "hp": character.growth_hp,
                "strength": character.growth_strength,
                "magic": character.growth_magic,
                "skill": character.growth_skill,
                "speed": character.growth_speed,
                "luck": character.growth_luck,
                "defense": character.growth_defense,
                "resistance": character.growth_resistance,
            }

            # Compute stats without class change
            expected_stats = {}
            base_class = character.base_class
            base_max_level = base_class.level_cap if form.cleaned_data["promoted"] and not base_class.promoted else level
            for stat in actual_stats.keys():
                expected_stats[stat] = expected_stat(base_stats[stat], growths[stat], character.base_level, base_max_level, getattr(base_class, stat))

            # If the character starts unpromoted but is promoted now, calculate promotion bonuses and expected promoted stats
            if form.cleaned_data["promoted"] and not base_class.promoted:
                promo_bonus = PromotionBonus.objects.filter(from_class=base_class).first()
                promo_class = promo_bonus.to_class
                for stat in actual_stats.keys():
                    expected_stats[stat] = calculate_promoted_stat(expected_stats[stat], getattr(promo_bonus, stat), getattr(promo_class, stat))
                    expected_stats[stat] = expected_stat(expected_stats[stat], growths[stat], 1, level, getattr(promo_class, stat))

            # assemble results
            results = {}
            for stat in actual_stats.keys():
                act = actual_stats[stat]
                exp = expected_stats[stat]
                diff = act - exp
                label = classify_stat(act, exp)

                results[stat] = {
                    "actual": act,
                    "expected": round(exp, 2),
                    "difference": round(diff, 2),
                    "label": label,
                }
    else:
        display_form = StatCheckForm()
    return render(request, "calculator/stat_check.html", {
        "form": display_form,
        "results": results,
    })
