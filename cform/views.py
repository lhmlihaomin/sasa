from django.shortcuts import render
from django.http import HttpResponse

from .models import CField, CFormType, CForm, CFormFieldValue 
from .forms import CBaseForm


def get_form(form_name, form_type_name):
    cft = CFormType.objects.get(name=form_type_name)
    cf = CForm()
    cf.name = form_name
    cf.form_type = cft
    return cf

# Create your views here.
def index(request):
    cft = CFormType.objects.get(name="ec2_config")
    cf = CForm()
    cf.name = "A Form"
    cf.form_type = cft
    print(cf.id)

    cform = CBaseForm()
    """for f in cf.form_type.ordered_fields:
        cform.fields.update({f.name: cform.map_field(f)})"""
    cform.set_fields(cf.form_type.ordered_fields)

    data = {}
    if request.method == 'POST':
        cform.set_data(request.POST)
        if cform.is_valid():
            data = cform.cleaned_data
            cf.save_data(data)

    return render(request, 'cform/index.html', {'form': cform, 'data': repr(data)})
    