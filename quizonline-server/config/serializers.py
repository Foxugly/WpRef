import json

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


class UserSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()


class DomainNameSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class LocalizedNameDescriptionTranslationSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()


class LocalizedQuestionTranslationSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    explanation = serializers.CharField()


class LocalizedAnswerOptionTranslationSerializer(serializers.Serializer):
    content = serializers.CharField()


class LocalizedQuestionTitleTranslationSerializer(serializers.Serializer):
    title = serializers.CharField()


class LocalizedSubjectTranslationSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    domain = DomainNameSummarySerializer()


class LocalizedSubjectDetailTranslationSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    domain_name = serializers.CharField()


class LocalizedQuizTemplateTranslationSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()


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


class TranslationMapSchemaMixin:
    def __init__(self, *args, value_serializer, component_name: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.value_serializer = value_serializer
        self.component_name = component_name


class TranslationMapInlineSchemaMixin:
    def __init__(self, *args, value_serializer, **kwargs):
        super().__init__(*args, **kwargs)
        self.value_serializer = value_serializer


class SerializerListSchemaMixin:
    def __init__(self, *args, item_serializer, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_serializer = item_serializer


class LocalizedTranslationsMapField(TranslationMapSchemaMixin, serializers.Field):
    pass


class LocalizedTranslationsDictField(TranslationMapInlineSchemaMixin, serializers.DictField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("child", serializers.DictField())
        super().__init__(*args, **kwargs)


class LocalizedTranslationsJSONField(TranslationMapInlineSchemaMixin, serializers.Field):
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


class SerializerListJSONField(SerializerListSchemaMixin, serializers.Field):
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


class NamedTranslationMapSchemaFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "config.serializers.LocalizedTranslationsMapField"

    def get_name(self) -> str:
        return self.target.component_name

    def map_serializer_field(self, auto_schema, direction):
        value_serializer = self.target.value_serializer
        if isinstance(value_serializer, type):
            value_serializer = value_serializer()
        component = auto_schema.resolve_serializer(value_serializer, direction)
        return {
            "type": "object",
            "additionalProperties": component.ref,
        }


class InlineTranslationMapSchemaFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "config.serializers.TranslationMapInlineSchemaMixin"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        value_serializer = self.target.value_serializer
        if isinstance(value_serializer, type):
            value_serializer = value_serializer()
        component = auto_schema.resolve_serializer(value_serializer, direction)
        return {
            "type": "object",
            "additionalProperties": component.ref,
        }


class SerializerListSchemaFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "config.serializers.SerializerListSchemaMixin"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        item_serializer = self.target.item_serializer
        if isinstance(item_serializer, type):
            item_serializer = item_serializer()
        component = auto_schema.resolve_serializer(item_serializer, direction)
        return {
            "type": "array",
            "items": component.ref,
        }


def localized_translations_map_schema(value_serializer, component_name: str) -> LocalizedTranslationsMapField:
    return LocalizedTranslationsMapField(
        value_serializer=value_serializer,
        component_name=component_name,
    )
