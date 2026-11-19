from django.views.generic import TemplateView


class AboutView(TemplateView):
    """Сторінка «Про програму» з відомостями про розробника."""

    template_name = "training/about.html"
