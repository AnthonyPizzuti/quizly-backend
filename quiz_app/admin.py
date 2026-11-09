from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.StackedInline):
    """Shows and edits the questions directly inside the quiz form."""

    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin configuration for quizzes including their questions."""

    list_display = ["title", "user", "created_at", "updated_at"]
    list_filter = ["created_at", "user"]
    search_fields = ["title", "description"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin configuration for editing single questions."""

    list_display = ["question_title", "quiz", "answer"]
    search_fields = ["question_title"]
    list_filter = ["quiz"]
