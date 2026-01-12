from rest_framework import serializers


class TranslateItemSerializer(serializers.Serializer):
    key = serializers.CharField()  # ex: "name", "description"
    text = serializers.CharField(allow_blank=True, required=True)
    format = serializers.ChoiceField(choices=["text", "html"], default="text")


class TranslateBatchRequestSerializer(serializers.Serializer):
    source = serializers.CharField(max_length=10)  # ex: "fr"
    target = serializers.CharField(max_length=10)  # ex: "nl"
    items = TranslateItemSerializer(many=True)


class TranslateBatchResponseSerializer(serializers.Serializer):
    translations = serializers.DictField(child=serializers.CharField())
