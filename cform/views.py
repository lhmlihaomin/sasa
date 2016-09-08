from django.shortcuts import render
from django.http import HttpResponse

from .models import CField, CFormType, CForm, CFormFieldValue 

# Create your views here.
def index(request):
    cft = CFormType.objects.get(pk=1)
    cf = CForm()
    cf.name = "A Form"
    cf.form_type = cft
    r = ""
    for f in cf.form_type.ordered_fields:
        r += "%s(%s)<br/>\n"%(
            f.name,
            f.field_type,
        )
    return HttpResponse(r)
    