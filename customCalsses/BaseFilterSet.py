from django_filters import rest_framework as filters
from django.db.models import ForeignKey, ManyToManyField, ImageField, FileField
from functools import partial
class BaseFilterSet(filters.FilterSet):
    """A base filter class that automatically creates filters for all fields, 
    including multi-value filtering for ForeignKey and ManyToMany fields."""

    @classmethod
    def filter_for_field(cls, f, name, lookup_expr):
        """Override default filter creation to ignore ImageField and FileField."""
        if isinstance(f, (ImageField, FileField)):
            return filters.CharFilter(method=lambda qs, name, value: qs)  # No-op filter
        return super().filter_for_field(f, name, lookup_expr)
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model = self.Meta.model

        for field in model._meta.get_fields():
            if isinstance(field, (ForeignKey, ManyToManyField)):
                field_name = field.name
                # Add support for filtering multiple values (comma-separated)
                self.filters[field_name] = filters.CharFilter(
                    method=partial(self.filter_multiple_values, field_name)
                )

    def filter_multiple_values(self, field_name, queryset, name, value):
        """Splits the input values by comma and applies `__in` filtering."""
        values = value.split(",")  # Split the string into a list of values
        return queryset.filter(**{f"{field_name}__in": values})
