from django import forms
from django.core.exceptions import ValidationError
from fe_data.models import Character


class StatCheckForm(forms.Form):
    character = forms.ModelChoiceField(
        queryset=Character.objects.all(), label="Character"
    )

    level = forms.IntegerField(min_value=1, max_value=20, label="Current Level")

    promoted = forms.BooleanField(label="Promoted", required=False)

    hp = forms.IntegerField(label="HP")
    strength = forms.IntegerField(label="Strength")
    magic = forms.IntegerField(label="Magic")
    skill = forms.IntegerField(label="Skill")
    speed = forms.IntegerField(label="Speed")
    luck = forms.IntegerField(label="Luck")
    defense = forms.IntegerField(label="Defense")
    resistance = forms.IntegerField(label="Resistance")

    def clean(self):
        cleaned_data = super().clean()
        character = cleaned_data.get("character")
        level = cleaned_data.get("level")
        if character.base_class.promoted:
            cleaned_data["promoted"] = True
            if level < character.base_level:
                self.add_error(
                    "level",
                    f"{character.name} must be at least level {character.base_level}.",
                )
        else:
            if level < character.base_level and cleaned_data["promoted"] == False:
                self.add_error(
                    "level",
                    f"An unpromoted {character.name} must be at least level {character.base_level}",
                )
        return cleaned_data
