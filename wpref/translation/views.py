from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .serializers import (
    TranslateBatchRequestSerializer,
    TranslateBatchResponseSerializer,
)
from .services.deepl import deepl_translate_many, DeepLError

def _is_effectively_empty_html(html: str) -> bool:
    s = (html or "").strip().lower()
    return (not s) or s in ["<p><br></p>", "<p></p>"]

class TranslateBatchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        req_ser = TranslateBatchRequestSerializer(data=request.data)
        req_ser.is_valid(raise_exception=True)
        data = req_ser.validated_data

        source = data["source"]
        target = data["target"]
        items = data["items"]

        # 1) Préparer les groupes (text/html)
        text_items = []
        html_items = []

        for it in items:
            key = it["key"]
            txt = it["text"] or ""
            fmt = it["format"]

            # optimisation : si vide, on renvoie vide sans appeler DeepL
            if fmt == "html" and _is_effectively_empty_html(txt):
                continue
            if fmt == "text" and not txt.strip():
                continue

            if fmt == "html":
                html_items.append((key, txt))
            else:
                text_items.append((key, txt))

        translations: dict[str, str] = {}

        try:
            # 2) Traduire le groupe TEXT en 1 appel DeepL
            if text_items:
                keys = [k for k, _ in text_items]
                texts = [t for _, t in text_items]
                out = deepl_translate_many(texts, source, target, fmt="text")
                for k, translated in zip(keys, out):
                    translations[k] = translated

            # 3) Traduire le groupe HTML en 1 appel DeepL
            if html_items:
                keys = [k for k, _ in html_items]
                texts = [t for _, t in html_items]
                out = deepl_translate_many(texts, source, target, fmt="html")
                for k, translated in zip(keys, out):
                    translations[k] = translated

        except DeepLError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        resp_ser = TranslateBatchResponseSerializer({"translations": translations})
        return Response(resp_ser.data, status=status.HTTP_200_OK)
