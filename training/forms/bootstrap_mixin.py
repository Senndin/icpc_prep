from django import forms


class BootstrapFormMixin:
    """Додає CSS-класи Bootstrap до віджетів форми."""

    def __init__(self, *args, **kwargs):
        """Ініціалізує форму та оформлює всі поля."""
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
