from rest_framework import serializers


class ChoiceDisplayFieldSerializer(serializers.ChoiceField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choice_strings_to_display = {str(key): value for key, value in self.choices.items()}
    
    def to_representation(self, value):
        response = {
            "value": self.choice_strings_to_values.get(str(value), value),
            "display_name": self.choice_strings_to_display.get(str(value), value),
        }
        return response
