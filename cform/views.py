from django.shortcuts import render
from django.http import HttpResponse

from .models import CField, CFormType, CForm, CFormFieldValue 
from .forms import CBaseForm

# Create your views here.
def index(request):
    cft = CFormType.objects.get(name="ec2_config")
    cf = CForm()
    cf.name = "A Form"
    cf.form_type = cft

    cform = CBaseForm()
    """for f in cf.form_type.ordered_fields:
        cform.fields.update({f.name: cform.map_field(f)})"""
    print(cf.form_type.ordered_fields)
    cform.set_fields(cf.form_type.ordered_fields)

    data = {}
    if request.method == 'POST':
        cform.set_data(request.POST)
        if cform.is_valid():
            data = cform.cleaned_data

    return render(request, 'cform/index.html', {'form': cform, 'data': repr(data)})
    