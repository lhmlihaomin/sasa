from django.shortcuts import render
from django.http import HttpResponse

from .models import CField, CFormType, CForm, CFormFieldValue 
from .forms import CBaseForm

# Create your views here.
def index(request):
    cft = CFormType.objects.get(pk=1)
    cf = CForm()
    cf.name = "A Form"
    cf.form_type = cft

    cform = CBaseForm()
    for f in cf.form_type.ordered_fields:
        cform.fields.update({f.name: cform.map_field(f)})

    r = ""
    for f in cf.form_type.ordered_fields:
        r += "%s(%s)<br/>\n"%(
            f.name,
            f.field_type,
        )
    return HttpResponse("<table>"+cform.as_table()+"</table>")
    