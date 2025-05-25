from django.shortcuts import render
from django.views.generic import TemplateView


class About(TemplateView):
    template_name = 'pages/about.html'


class Rules(TemplateView):
    template_name = 'pages/rules.html'


def page_not_found(request, exception):
    template = 'pages/404.html'
    return render(request, template, status=404)


def csrf_failure(request, reason=''):
    template = 'pages/403csrf.html'
    return render(request, template, status=403)


def server_error(request, exception=None):
    template = 'pages/500.html'
    return render(request, template, status=500)
