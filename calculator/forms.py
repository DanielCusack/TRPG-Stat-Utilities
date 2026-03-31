from django import forms
from fe_data.models import Character

class StatCheckForm(forms.Form):
    character = forms.ModelChoiceField(
        queryset=Character.objects.all(),
        label="Character"
    )

    level = forms.IntegerField(
        min_value=1,
        max_value=20,
        label="Current Level"
    )

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
        if character.base_class.promoted:
            cleaned_data["promoted"] = True
        return cleaned_data

