# question/views.py
import json

from django.http import QueryDict  # ⬅️ AJOUT
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import Question, QuestionMedia
from .serializers import QuestionSerializer

TEST = True


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.prefetch_related("media", "answer_options", "subjects")
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["title", "description"]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        return [IsAdminUser()]

    def _coerce_json_fields(self, data):
        """
        Transforme request.data (QueryDict) en dict normal pour le serializer,
        en gérant correctement :
        - subject_ids  -> liste d'int
        - answer_options -> liste de dicts (parse JSON)
        """

        # 1) On sort de la QueryDict -> dict Python classique
        if isinstance(data, QueryDict):
            mutable = {}

            for key in data.keys():
                if key == "subject_ids":
                    # subject_ids peut apparaître plusieurs fois : getlist()
                    # ex: ['3', '1', '2\n'] -> [3, 1, 2]
                    mutable["subject_ids"] = [
                        int(v) for v in data.getlist("subject_ids") if v.strip()
                    ]
                else:
                    # pour les autres champs (title, description, answer_options, …)
                    # on prend la première valeur
                    mutable[key] = data.get(key)
        else:
            mutable = dict(data)

        # 2) answer_options : string JSON -> liste de dicts
        raw_answer_options = mutable.get("answer_options")
        if isinstance(raw_answer_options, str):
            try:
                parsed = json.loads(raw_answer_options)
                if isinstance(parsed, list):
                    # Là on a bien [{...}, {...}], pas [[{...}]]
                    mutable["answer_options"] = parsed
            except json.JSONDecodeError:
                # si ce n'est pas du JSON valide, on laisse tomber
                pass

        # (optionnel) même traitement pour media si tu l'envoies en JSON
        raw_media = mutable.get("media")
        if isinstance(raw_media, str):
            try:
                parsed_media = json.loads(raw_media)
                if isinstance(parsed_media, list):
                    mutable["media"] = parsed_media
            except json.JSONDecodeError:
                pass

        return mutable

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(title__icontains=search)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = self._coerce_json_fields(request.data)
        media_data = data.get("media", [])
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            print("CREATE errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        question = serializer.save()
        self._handle_media_upload(request, question, media_data=media_data)
        return Response(self.get_serializer(question).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.get("partial", False)
        instance = self.get_object()
        data = self._coerce_json_fields(request.data)
        media_data = data.get("media", [])
        serializer = self.get_serializer(instance, data=data, partial=partial)
        if not serializer.is_valid():
            print("UPDATE errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        question = serializer.save()
        self._handle_media_upload(request, question, media_data=media_data)
        return Response(self.get_serializer(question).data, status=status.HTTP_200_OK)

    # ---------------------------
    # Gestion des médias
    # ---------------------------
    def _handle_media_upload(self, request, question: Question, media_data=None) -> None:
        """
        Reconstruit entièrement les médias d'une question à partir de :
        - request.FILES (images / vidéos)
        - request.data (liens externes, ex: YouTube)

        Convention côté frontend (Angular) :
        - fichiers envoyés en multipart sous des clés du style:
            media[0][file], media[1][file], ...
        - liens externes envoyés sous des clés:
            media[0][external_url], media[1][external_url], ...
          ou éventuellement un champ global "youtube_url".
        """

        # 1) On nettoie les anciens médias
        question.media.all().delete()

        sort_index = 1
        media_data = media_data or []
        # 2) Fichiers uploadés (image / vidéo)
        #    On parcourt toutes les clés de FILES (peu importe leur nom exact)
        for key in request.FILES:
            for f in request.FILES.getlist(key):
                content_type = (getattr(f, "content_type", "") or "").lower()
                if content_type.startswith("image/"):
                    kind = QuestionMedia.IMAGE
                elif content_type.startswith("video/"):
                    kind = QuestionMedia.VIDEO
                else:
                    # on ignore les MIME non supportés
                    continue

                QuestionMedia.objects.create(
                    question=question,
                    kind=kind,
                    file=f,
                    sort_order=sort_index,
                )
                sort_index += 1

        # 3) Liens externes : on utilise media_data PARSÉ, pas request.data['media']
        for item in media_data:
            # sécurité : on ignore les trucs qui ne sont pas des dicts
            if not isinstance(item, dict):
                continue

            if item.get("kind") == QuestionMedia.EXTERNAL and item.get("external_url"):
                QuestionMedia.objects.create(
                    question=question,
                    kind=QuestionMedia.EXTERNAL,
                    external_url=item["external_url"],
                    sort_order=item.get("sort_order", sort_index),
                )
                sort_index += 1
