from django.shortcuts import render
from .forms import StatCheckForm
from .utils import classify_stat


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

            expected_stats = character.calculate_expected_stats(
                level, form.cleaned_data["promoted"]
            )
            percentile_stats = character.calculate_stat_percentiles(
                actual_stats, level, form.cleaned_data["promoted"]
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
                    "label": percentile_stats,
                }
    else:
        display_form = StatCheckForm()
    return render(
        request,
        "calculator/stat_check.html",
        {
            "form": display_form,
            "results": results,
        },
    )
