from django import forms

from .models import CField

class CBaseForm(forms.Form):
    pass

    def map_field(self, cfield):
        label = cfield.title
        if cfield.required:
            suffix = "*"

        if cfield.field_type == "string":
            f = forms.CharField(required=cfield.required,
                                label=label,
                                label_suffix=suffix)
        elif cfield.field_type == "text":
            f = forms.CharField(required=cfield.required, 
                                widget=forms.Textarea, 
                                label=label,
                                label_suffix=suffix)
        elif cfield.field_type == "email":
            f = forms.EmailField(required=cfield.required, 
                                 label=label,
                                 label_suffix=suffix)
        elif cfield.field_type == "boolean":
            f = forms.BooleanField(required=cfield.required, 
                                   label=label,
                                   label_suffix=suffix)
        elif cfield.field_type == "number":
            f = forms.FloatField(required=cfield.required, 
                                 label=label,
                                 label_suffix=suffix)
        elif cfield.field_type == "integer":
            f = forms.IntegerField(required=cfield.required, 
                                   label=label,
                                   label_suffix=suffix)
        elif cfield.field_type == "select":
            f = forms.ChoiceField(required=cfield.required, 
                                  choices=cfield.choices, 
                                  label=label,
                                  label_suffix=suffix)
        elif cfield.field_type == "select_multiple":
            f = forms.MultipleChoiceField(required=cfield.required, 
                                          choices=cfield.choices, 
                                          label=label,
                                          label_suffix=suffix)
        elif cfield.field_type == "checkbox":
            f = forms.BooleanField(required=cfield.required, 
                                   label=label,
                                   label_suffix=suffix)
        elif cfield.field_type == "radio":
            f = forms.ChoiceField(required=cfield.required, 
                                  choices=cfield.choices, 
                                  widget=forms.RadioSelect, 
                                  label=label,
                                  label_suffix=suffix)
        else:
            # return a generic text input:
            f = forms.CharField()
        print(f.label_suffix)
        return f


    def set_fields(self, ordered_fields):
        for f in ordered_fields:
            self.fields.update({f.title: self.map_field(f)})


    def set_data(self, post_data):
        # find each field and set its data:
        for key in post_data:
            print(key)
            if self.fields.has_key(key):
                self.data[key] = post_data[key]
        
        # don't forget to set this, or this form is never valid:
        self.is_bound = True
