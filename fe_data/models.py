from django.db import models

from fe_data.constants import FE_STAT_NAMES
from calculator.utils import (
    expected_stat,
    calculate_promoted_stat,
    cumulative_binomial_probability_at_least,
    binomial_probability,
)


class StatBlock(models.Model):
    hp = models.IntegerField()
    strength = models.IntegerField()
    magic = models.IntegerField()
    skill = models.IntegerField()
    speed = models.IntegerField()
    luck = models.IntegerField()
    defense = models.IntegerField()
    resistance = models.IntegerField()

    class Meta:
        abstract = True


class FEClass(StatBlock):
    name = models.CharField(max_length=50)
    level_cap = models.IntegerField(default=20)
    promoted = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class PromotionBonus(StatBlock):
    from_class = models.ForeignKey(
        FEClass, on_delete=models.CASCADE, related_name="promotes_from"
    )
    to_class = models.ForeignKey(
        FEClass, on_delete=models.CASCADE, related_name="promotes_to"
    )

    def __str__(self):
        return f"{self.from_class} → {self.to_class}"


class Character(models.Model):
    name = models.CharField(max_length=50)
    base_class = models.ForeignKey(FEClass, on_delete=models.CASCADE)

    # Base stats
    base_level = models.IntegerField(default=1)
    base_hp = models.IntegerField()
    base_strength = models.IntegerField()
    base_magic = models.IntegerField()
    base_skill = models.IntegerField()
    base_speed = models.IntegerField()
    base_luck = models.IntegerField()
    base_defense = models.IntegerField()
    base_resistance = models.IntegerField()

    # Growth rates (percent)
    growth_hp = models.FloatField()
    growth_strength = models.FloatField()
    growth_magic = models.FloatField()
    growth_skill = models.FloatField()
    growth_speed = models.FloatField()
    growth_luck = models.FloatField()
    growth_defense = models.FloatField()
    growth_resistance = models.FloatField()

    def calculate_expected_stats(self, level: int, promoted: bool):
        """Calculate the character's expected stats for a given level and promotion via growths X level."""
        # Compute stats without class change
        expected_stats = {}
        base_max_level = (
            self.base_class.level_cap
            if promoted and not self.base_class.promoted
            else level
        )
        for stat in FE_STAT_NAMES:
            expected_stats[stat] = expected_stat(
                getattr(self, "base_" + stat),
                getattr(self, "growth_" + stat),
                self.base_level,
                base_max_level,
                getattr(self.base_class, stat),
            )

        # If the character starts unpromoted but is promoted now, calculate promotion bonuses and expected promoted stats
        if promoted and not self.base_class.promoted:
            promo_bonus = PromotionBonus.objects.filter(
                from_class=self.base_class
            ).first()
            promo_class = promo_bonus.to_class
            for stat in FE_STAT_NAMES:
                expected_stats[stat] = calculate_promoted_stat(
                    expected_stats[stat],
                    getattr(promo_bonus, stat),
                    getattr(promo_class, stat),
                )
                expected_stats[stat] = expected_stat(
                    expected_stats[stat],
                    getattr(self, "growth_" + stat),
                    1,
                    level,
                    getattr(promo_class, stat),
                )
        return expected_stats

    def calculate_stat_percentiles(
        self, stats: dict[str, int], level: int, promoted: bool
    ):
        stat_percentiles = {}
        if promoted and not self.base_class.promoted:
            unpromoted_lvls = self.base_class.level_cap - self.base_level
            p_bonus_info = PromotionBonus.objects.get(from_class=self.base_class)
            pclass = p_bonus_info.to_class
            promoted_lvls = level - 1
            total_levels = unpromoted_lvls + promoted_lvls
            for stat_name in FE_STAT_NAMES:
                growth_percentage = getattr(self, "growth_" + stat_name)
                guaranteed_stat_per_level = int(growth_percentage // 100)
                growth_probability = (
                    growth_percentage / 100
                ) - guaranteed_stat_per_level
                base_class_cap = getattr(self.base_class, stat_name)
                base_stat = getattr(self, "base_" + stat_name)
                promo_bonus = getattr(p_bonus_info, stat_name)
                if (
                    base_stat + unpromoted_lvls * (guaranteed_stat_per_level + 1)
                    > base_class_cap
                ):
                    # If the character can cap in their unpromoted class then we
                    # can calculate the percentile by treating the paths where the
                    # character caps separately from those where it doesn't.
                    stat_ups_required = (
                        stats[stat_name]
                        - base_stat
                        - min(
                            base_class_cap - base_stat,
                            guaranteed_stat_per_level * unpromoted_lvls,
                        )
                        - (guaranteed_stat_per_level * promoted_lvls)
                        - promo_bonus
                    )
                    if stat_ups_required < 1:
                        # Technically, if the stat is at or below the minimum possible,
                        # then 100% of samples will have at least that amount
                        stat_percentiles[stat_name] = 1
                        continue
                    percentile = 0
                    # start by calculating the non-cap contribution if any

                    # Sum staring from minimum required stat ups where it is still
                    # possible to hit the expected stat value when promoted and leveled
                    # to the given level.
                    low_non_cap_level = max(
                        (
                            stats[stat_name]
                            - base_stat
                            - promo_bonus
                            - promoted_lvls * (1 + guaranteed_stat_per_level)
                            - unpromoted_lvls * guaranteed_stat_per_level
                        ),
                        0,
                    )

                    # to the maximum number of unpromoted stat ups before hitting
                    # the unpromoted cap
                    high_non_cap_level = (
                        base_class_cap
                        - base_stat
                        - unpromoted_lvls * guaranteed_stat_per_level
                        - 1
                    )
                    if high_non_cap_level >= low_non_cap_level:
                        promo_lower_bound = (
                            stats[stat_name]
                            - base_stat
                            - promo_bonus
                            - guaranteed_stat_per_level * total_levels
                        )
                        for i in range(low_non_cap_level, high_non_cap_level + 1):
                            percentile += binomial_probability(
                                unpromoted_lvls, i, growth_probability
                            ) * cumulative_binomial_probability_at_least(
                                promoted_lvls, promo_lower_bound - i, growth_probability
                            )

                    # Lastly calculate the cap contribution
                    promo_lower_bound = (
                        stats[stat_name]
                        - base_class_cap
                        - promo_bonus
                        - guaranteed_stat_per_level * promoted_lvls
                    )
                    promoted_cap_probability = cumulative_binomial_probability_at_least(
                        promoted_lvls, promo_lower_bound, growth_probability
                    )
                    if high_non_cap_level >= 0:
                        percentile += (
                            cumulative_binomial_probability_at_least(
                                unpromoted_lvls,
                                high_non_cap_level + 1,
                                growth_probability,
                            )
                            * promoted_cap_probability
                        )
                    else:
                        # The the stat is guaranteed to cap, just add the
                        # promoted_cap_probability
                        percentile += promoted_cap_probability
                    stat_percentiles[stat_name] = percentile
                else:
                    # The simple case. We can treat it as a binomial distribution
                    # where the number of trials is equal to the sum of
                    # unpromoted and promoted level ups

                    stat_ups_required = (
                        stats[stat_name]
                        - base_stat
                        - (guaranteed_stat_per_level * total_levels)
                        - promo_bonus
                    )
                    if stat_ups_required < 1:
                        # Technically, if the stat is at or below the minimum possible,
                        # then 100% of samples will have at least that amount
                        stat_percentiles[stat_name] = 1
                        continue
                    stat_percentiles[stat_name] = (
                        cumulative_binomial_probability_at_least(
                            total_levels, stat_ups_required, growth_probability
                        )
                    )
        else:
            # The simple case. we can treat it as a binomial distribution
            level_up_number = level - self.base_level
            for stat_name in FE_STAT_NAMES:
                growth_percentage = getattr(self, "growth_" + stat_name)
                guaranteed_stat_per_level = int(growth_percentage // 100)
                growth_probability = (
                    growth_percentage / 100
                ) - guaranteed_stat_per_level
                stat_ups_required = (
                    stats[stat_name]
                    - getattr(self, "base_" + stat_name)
                    - (guaranteed_stat_per_level * level_up_number)
                )
                if stat_ups_required < 1:
                    # Technically, if the stat is at or below the minimum possible,
                    # then 100% of samples will have at least that amount
                    stat_percentiles[stat_name] = 1
                    continue
                growth_percentage = getattr(self, "growth_" + stat_name)

                stat_percentiles[stat_name] = cumulative_binomial_probability_at_least(
                    level_up_number, stat_ups_required, growth_probability
                )
        return stat_percentiles

    def __str__(self):
        return self.name
