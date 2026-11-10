"""Helper functions to create a quiz from a YouTube video."""

import json
import os
import re
import tempfile
from functools import lru_cache

import whisper
import yt_dlp
from django.conf import settings
from django.db import transaction
from google import genai
from google.genai import types

from quiz_app.models import Question, Quiz

YOUTUBE_ID_PATTERN = re.compile(
    r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/)|youtu\.be/)"
    r"([A-Za-z0-9_-]{11})"
)
WHISPER_MODEL_NAME = "base"
GEMINI_MODEL_NAME = "gemini-3.7-flash"

QUIZ_PROMPT = """
Based on the following transcript, generate a quiz in valid JSON format.
Write the quiz in the same language as the transcript.

The quiz must follow this exact structure:
{{
  "title": "Create a concise quiz title based on the topic of the transcript.",
  "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
  "questions": [
    {{
      "question_title": "The question goes here.",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct answer from the above options"
    }},
    ...
    (exactly 10 questions)
  ]
}}

Requirements:
- Each question must have exactly 4 distinct answer options.
- Only one correct answer is allowed per question, and it must be present in 'question_options'.
- The output must be valid JSON and parsable as-is (e.g., using Python's json.loads).
- Do not include explanations, comments, or any text outside the JSON.

Transcript:
{transcript}
"""


def extract_video_id(url):
    """Return the 11-character YouTube video ID or None if the URL is invalid."""
    match = YOUTUBE_ID_PATTERN.search(url or "")
    return match.group(1) if match else None


def build_video_url(video_id):
    """Build the normalized YouTube URL that is stored in the database."""
    return f"https://www.youtube.com/watch?v={video_id}"


def download_audio(video_url, tmp_filename):
    """Download only the audio track of the YouTube video."""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": tmp_filename,
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])


@lru_cache(maxsize=1)
def get_whisper_model():
    """Load the Whisper model once and reuse it for every request."""
    return whisper.load_model(WHISPER_MODEL_NAME)


def transcribe_audio(audio_path):
    """Transcribe the audio file locally with Whisper and return the text."""
    result = get_whisper_model().transcribe(audio_path, fp16=False)
    return result["text"]


def get_transcript(video_url):
    """Download the audio into a temporary folder and return its transcript."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_filename = os.path.join(tmp_dir, "audio")
        download_audio(video_url, tmp_filename)
        return transcribe_audio(tmp_filename)


def clean_json_response(text):
    """Remove Markdown code fences like ```json from the AI response."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    return re.sub(r"\s*```$", "", cleaned)


def generate_quiz_data(transcript):
    """Let Gemini Flash create the quiz and return it as a dictionary."""
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=3)
        ),
    )
    response = client.models.generate_content(
        model=GEMINI_MODEL_NAME,
        contents=QUIZ_PROMPT.format(transcript=transcript),
        config={"response_mime_type": "application/json"},
    )
    return json.loads(clean_json_response(response.text))


def is_valid_question(question):
    """Check that a question has a title, 4 options and a valid answer."""
    options = question.get("question_options", [])
    has_title = bool(question.get("question_title"))
    return has_title and len(options) == 4 and question.get("answer") in options


def is_valid_quiz_data(quiz_data):
    """Check that the AI result has a title and exactly 10 valid questions."""
    questions = quiz_data.get("questions", [])
    if not quiz_data.get("title") or len(questions) != 10:
        return False
    return all(is_valid_question(question) for question in questions)


@transaction.atomic
def save_quiz(user, video_url, quiz_data):
    """Save the quiz and its questions in the database."""
    quiz = Quiz.objects.create(
        user=user,
        title=quiz_data["title"],
        description=quiz_data.get("description", ""),
        video_url=video_url,
    )
    Question.objects.bulk_create(
        [build_question(quiz, question) for question in quiz_data["questions"]]
    )
    return quiz


def build_question(quiz, question):
    """Create an unsaved Question object from the AI question data."""
    return Question(
        quiz=quiz,
        question_title=question["question_title"],
        question_options=question["question_options"],
        answer=question["answer"],
    )


def create_quiz_from_url(user, video_url):
    """Run the full pipeline: audio, transcript, AI quiz, database."""
    transcript = get_transcript(video_url)
    quiz_data = generate_quiz_data(transcript)
    if not is_valid_quiz_data(quiz_data):
        raise ValueError("The AI returned an invalid quiz.")
    return save_quiz(user, video_url, quiz_data)
