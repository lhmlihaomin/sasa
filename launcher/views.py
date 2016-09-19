import collections

from django.shortcuts import render

# Create your views here.
def index(request):
    modules = {
        "account": [
            ["account", "1.1.1", "aps1", "a"],
            ["account", "1.1.2", "aps1", "a"],
        ],
        "connector": [
            ["connector", "2.0.8", "aps1", "a"],
            ["connector", "2.0.9", "aps1", "a"],
        ],
        "device": [
            ["device", "2.1.12", "aps1", "a"],
            ["device", "2.1.13", "aps1", "a"],
        ],
        "appservice_pushservice": [
            ["appservice_pushservice", "1.0.0_1.0.0", "aps1", "a"],
            ["appservice_pushservice", "1.0.1_1.0.1", "aps1", "a"],
        ]

    }
    return render(request, "launcher/index.html", {"modules": modules})