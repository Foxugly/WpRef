import json
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers


@extend_schema_field(OpenApiTypes.OBJECT)
class JSONDictOrStringField(serializers.Field):
    """
    Accepte soit un dict, soit une string JSON représentant un dict.
    (utile pour multipart/form-data)
    """
    def to_internal_value(self, data):
        if data is None or data == "":
            return {}
        if isinstance(data, dict):
            return data
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON object.")
            if not isinstance(parsed, dict):
                raise serializers.ValidationError("Expected a JSON object.")
            return parsed
        raise serializers.ValidationError("Expected object or JSON string.")

    def to_representation(self, value):
        return value


@extend_schema_field(serializers.ListField(child=serializers.DictField()))
class JSONListOrStringField(serializers.Field):
    """
    Accepte soit une list, soit une string JSON représentant une list.
    """
    def to_internal_value(self, data):
        if data is None or data == "":
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON array.")
            if not isinstance(parsed, list):
                raise serializers.ValidationError("Expected a JSON array.")
            return parsed
        raise serializers.ValidationError("Expected array or JSON string.")

    def to_representation(self, value):
        return value
