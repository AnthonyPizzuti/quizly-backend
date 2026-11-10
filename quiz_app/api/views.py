from rest_framework import generics, status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from yt_dlp.utils import DownloadError

from quiz_app.models import Quiz
from quiz_app.utils import create_quiz_from_url
from .permissions import IsQuizOwner
from .serializers import (
    QuizCreateResponseSerializer,
    QuizCreateSerializer,
    QuizSerializer,
)


class QuizListCreateView(APIView):
    """Lists the user's quizzes and creates new ones from YouTube URLs."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all quizzes of the authenticated user."""
        quizzes = Quiz.objects.filter(user=request.user)
        quizzes = quizzes.prefetch_related("questions")
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Generate a quiz from the given YouTube URL and return it."""
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video_url = serializer.validated_data["url"]
        try:
            quiz = create_quiz_from_url(request.user, video_url)
        except DownloadError:
            raise ValidationError({"url": "Video could not be downloaded."})
        except Exception:
            raise APIException("Quiz could not be created.")
        data = QuizCreateResponseSerializer(quiz).data
        return Response(data, status=status.HTTP_201_CREATED)


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieves, partially updates or deletes a single quiz of the user."""

    queryset = Quiz.objects.prefetch_related("questions")
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsQuizOwner]
    http_method_names = ["get", "patch", "delete"]
