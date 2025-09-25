
from rest_framework import serializers
from django.db.models import ForeignKey, OneToOneField, ManyToManyField
import re

class DynamicExpandMixin(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request:
            return data
        expand_map = self._build_expand_map(request.query_params.get('expand', ''))
        for field in self.Meta.model._meta.get_fields():
            if field.name in expand_map and isinstance(field, (ForeignKey, OneToOneField, ManyToManyField)):
                related_object = getattr(instance, field.name)
                if related_object:
                    if isinstance(field, ManyToManyField):
                        data[field.name] = [self._serialize_related_object(obj, expand_map[field.name])
                                            for obj in related_object.all()]
                    else:
                        data[field.name] = self._serialize_related_object(related_object, expand_map[field.name])
        return data

    def _serialize_related_object(self, obj, nested_expansions):
        serializer_class = self._get_dynamic_serializer(obj, nested_expansions)
        return serializer_class(obj, context=self.context).data

    def _get_dynamic_serializer(self, obj, nested_expansions):
        class DynamicSerializer(serializers.ModelSerializer):
            class Meta:
                model = obj.__class__
                fields = nested_expansions.get('__fields__', '__all__')

            def to_representation(serializer_self, instance):
                data = super(DynamicSerializer, serializer_self).to_representation(instance)
                for nested_field, nested_data in nested_expansions.items():
                    if nested_field == '__fields__':
                        continue
                    related_object = getattr(instance, nested_field, None)
                    if related_object:
                        if isinstance(related_object, (list, tuple)):
                            data[nested_field] = [self._serialize_related_object(obj, nested_data)
                                                  for obj in related_object]
                        else:
                            data[nested_field] = self._serialize_related_object(related_object, nested_data)
                return data
        return DynamicSerializer

    def _build_expand_map(self, expand_param):
        expand_map = {}
        expand_pattern = re.compile(r'(\w+)(?:\((.*?)\))?')
        for item in expand_param.split(','):
            parts = item.split('.')
            current = expand_map
            for index, part in enumerate(parts):
                match = expand_pattern.match(part)
                if match:
                    field_name = match.group(1)
                    fields_str = match.group(2)
                    if field_name not in current:
                        current[field_name] = {}
                    if fields_str:
                        fields = fields_str.split(',')
                        current[field_name]['__fields__'] = fields
                    current = current[field_name]
        return expand_map

class CustomBaseModelSerializer(DynamicExpandMixin, serializers.ModelSerializer):
    pass
