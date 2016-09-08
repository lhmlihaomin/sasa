from django import forms

from .models import CField

class CBaseForm(forms.Form):
    pass

    def map_field(self, cfield):
        if cfield.field_type == "string":
            f = forms.CharField(required=cfield.required)
        elif cfield.field_type == "text":
            f = forms.CharField(required=cfield.required, widget=forms.Textarea)
        elif cfield.field_type == "email":
            f = forms.EmailField(required=cfield.required)
        elif cfield.field_type == "boolean":
            f = forms.BooleanField(required=cfield.required)
        elif cfield.field_type == "number":
            f = forms.FloatField(required=cfield.required)
        elif cfield.field_type == "integer":
            f = forms.IntegerField(required=cfield.required)
        elif cfield.field_type == "select":
            f = forms.ChoiceField(required=cfield.required, choices=cfield.choices)
        elif cfield.field_type == "select_multiple":
            f = forms.ChoiceField(required=cfield.required, choices=cfield.choices)
        elif cfield.field_type == "checkbox":
            pass
        elif cfield.field_type == "radio":
            pass
        else:
            # return a generic text input:
            f = forms.CharField()
        return f