# question/views.py
import json

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
        Quand la requête vient de FormData, certaines valeurs arrivent
        comme des strings JSON. On les convertit en vrais objets Python.
        """
        mutable = data.copy()

        for field in ("subject_ids", "answer_options", "media"):
            if field in mutable:
                value = mutable.get(field)
                if isinstance(value, str):
                    try:
                        mutable[field] = json.loads(value)
                    except json.JSONDecodeError:
                        # on laisse tel quel si ce n'est pas du JSON
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
        print("QuestionViewSet CREATE:", request.data)

        data = self._coerce_json_fields(request.data) if TEST else request.data
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            print("CREATE errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        question = serializer.save()
        self._handle_media_upload(request, question)
        return Response(self.get_serializer(request, question).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        print("QuestionViewSet Update")
        partial = kwargs.get("partial", False)
        instance = self.get_object()
        print("AVANT")

        print(request.data)
        data = self._coerce_json_fields(request.data) if TEST else request.data
        print("APRES")
        print(data)
        print("APPEL SERIALIZER")
        serializer = self.get_serializer(instance, data=data, partial=partial)
        print("RESULTAT SERIALIZER")
        print(serializer)
        if not serializer.is_valid():
            print("UPDATE errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        question = serializer.save()
        self._handle_media_upload(request, question)
        return Response(self.get_serializer(question).data, status=status.HTTP_200_OK)

    # ---------------------------
    # Gestion des médias
    # ---------------------------
    def _handle_media_upload(self, request, question: Question) -> None:
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
        print("_HANDLE_MEDIA_UPLOAD - DATA:", request.data)
        print("_HANDLE_MEDIA_UPLOAD - FILES:", request.FILES)
        question.media.all().delete()

        sort_index = 1

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

        # 3) Liens externes `media[x][external_url]`
        if 'media' in request.data:
            for value in request.data['media']:
                if value["kind"] == QuestionMedia.EXTERNAL:
                    QuestionMedia.objects.create(
                        question=question,
                        kind=QuestionMedia.EXTERNAL,
                        external_url=value['external_url'],
                        sort_order=sort_index,
                    )
                    sort_index += 1
