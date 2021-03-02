from django.shortcuts import render
from django.http import HttpResponse


# TODO: remove this?


def index(request):
    return HttpResponse("Hello")
