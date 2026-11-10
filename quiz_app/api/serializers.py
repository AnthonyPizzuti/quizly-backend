from rest_framework import serializers

from quiz_app.models import Question, Quiz
from quiz_app.utils import build_video_url, extract_video_id


class QuestionSerializer(serializers.ModelSerializer):
    """Serializes a question without timestamps (list, detail, update)."""

    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer"]


class QuestionWithTimestampsSerializer(serializers.ModelSerializer):
    """Serializes a question including timestamps (create response)."""

    class Meta:
        model = Question
        fields = [
            "id",
            "question_title",
            "question_options",
            "answer",
            "created_at",
            "updated_at",
        ]


class QuizSerializer(serializers.ModelSerializer):
    """Serializes a quiz with its questions; only title and description are editable."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "video_url"]


class QuizCreateResponseSerializer(QuizSerializer):
    """Serializes a newly created quiz including question timestamps."""

    questions = QuestionWithTimestampsSerializer(many=True, read_only=True)


class QuizCreateSerializer(serializers.Serializer):
    """Validates the YouTube URL and returns it in normalized form."""

    url = serializers.CharField()

    def validate_url(self, value):
        """Extract the video ID and build the normalized YouTube URL."""
        video_id = extract_video_id(value)
        if video_id is None:
            raise serializers.ValidationError("Invalid YouTube URL.")
        return build_video_url(video_id)
