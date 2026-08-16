from django.shortcuts import render
from django.templatetags.static import static
from fe_data.constants import FE_STAT_NAMES
from fe_data.domain.statistics import (
    calculate_expected_stats,
    calculate_stat_percentiles,
)
from fe_data.models import Character
from .forms import StatCheckForm
from .portraits import available_portraits, default_portrait_path, portrait_path


def stat_check_view(request):
    results = None

    if request.method == "POST":
        form = StatCheckForm(request.POST)
        if form.is_valid():
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

            expected_stats = calculate_expected_stats(
                character, level, form.cleaned_data["promoted"]
            )
            percentile_stats = calculate_stat_percentiles(
                character, actual_stats, level, form.cleaned_data["promoted"]
            )

            # assemble results
            results = {}
            for stat in actual_stats.keys():
                act = actual_stats[stat]
                exp = expected_stats[stat]
                diff = act - exp

                results[stat] = {
                    "actual": act,
                    "expected": round(exp, 2),
                    "difference": round(diff, 2),
                    "percentile": round(100 * percentile_stats[stat], 2),
                }
    else:
        form = StatCheckForm()

    available = available_portraits()
    character_data = {
        c.pk: {
            "base": {stat: getattr(c, "base_" + stat) for stat in FE_STAT_NAMES},
            "growth": {stat: getattr(c, "growth_" + stat) for stat in FE_STAT_NAMES},
            "promoted": c.base_class.promoted,
            "can_promote": c.can_promote,
            "portrait": static(portrait_path(c.name, available)),
        }
        for c in Character.objects.select_related("base_class").all()
    }

    return render(
        request,
        "calculator/stat_check.html",
        {
            "form": form,
            "results": results,
            "character_data": character_data,
            "default_portrait": static(default_portrait_path()),
        },
    )
