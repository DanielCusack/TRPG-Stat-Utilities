from django.db import models


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
    from_class = models.ForeignKey(FEClass, on_delete=models.CASCADE, related_name="promotes_from")
    to_class = models.ForeignKey(FEClass, on_delete=models.CASCADE, related_name="promotes_to")

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

    def __str__(self):
        return self.name

