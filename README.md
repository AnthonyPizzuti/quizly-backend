# Quizly Backend

Quizly turns YouTube videos into quizzes. The user pastes a YouTube link, the backend
downloads the audio, transcribes it locally with Whisper AI and lets Gemini Flash
create a quiz with 10 questions and 4 answer options each.

This repository contains the **Django REST API**. The frontend is provided separately
and communicates with this backend via REST.

## Features

- Registration, login and logout with **JWT stored in HTTP-only cookies**
- Token refresh and **token blacklist** on logout
- Quiz generation from a YouTube URL: **yt-dlp → Whisper → Gemini Flash**
- Normalized YouTube URLs (`youtu.be`, `shorts`, `&t=…` etc. are all supported)
- List, view, edit (title/description) and delete your own quizzes
- Admin panel to edit quizzes and single questions

## Tech Stack

- Python, Django, Django REST Framework
- djangorestframework-simplejwt (JWT + blacklist)
- django-cors-headers
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading the audio
- [OpenAI Whisper](https://github.com/openai/whisper) for local transcription
- [Google Gen AI SDK](https://github.com/googleapis/python-genai) with Gemini Flash

## Requirements

> **Important:** FFmpeg must be installed **globally**. Whisper needs it to read
> the audio files. Without FFmpeg the quiz generation will not work.

| Tool | Why | Installation (Windows) |
|---|---|---|
| Python 3.12+ | Runs the backend (tested with 3.14) | [python.org](https://www.python.org/downloads/) |
| **FFmpeg** | Required by Whisper AI | `winget install Gyan.FFmpeg` |
| **Deno** | Used by yt-dlp to solve YouTube's JavaScript challenges | `winget install DenoLand.Deno` |
| Gemini API key | Quiz generation with Gemini Flash (free) | [Google AI Studio](https://aistudio.google.com/apikey) |

On macOS use `brew install ffmpeg deno`, on Linux use your package manager.
Check the installation with:

```bash
ffmpeg -version
deno --version
```

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/AnthonyPizzuti/quizly-backend.git
   cd quizly-backend
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv env
   ```

   Windows:

   ```bash
   env\Scripts\activate
   ```

   macOS / Linux:

   ```bash
   source env/bin/activate
   ```

3. **Install the dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   This also installs PyTorch for Whisper and can take a few minutes.

4. **Create the `.env` file**

   Copy `.env.example` to `.env` and fill in your own values:

   ```
   SECRET_KEY=your_django_secret_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

   You can generate a new Django secret key with:

   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

   Never commit the `.env` file. It is already listed in `.gitignore`.

5. **Apply the migrations and create an admin user**

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Start the server**

   ```bash
   python manage.py runserver
   ```

   The API is now available at `http://127.0.0.1:8000/api/`
   and the admin panel at `http://127.0.0.1:8000/admin/`.

## Connecting the frontend

- Start the frontend with e.g. VS Code **Live Server** on port `5500`.
- Open it via `http://127.0.0.1:5500` (not `localhost`), so the auth cookies
  match the backend address `127.0.0.1:8000`.
- Allowed frontend origins are configured in `CORS_ALLOWED_ORIGINS`
  in `core/settings.py`.

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/register/` | Register a new user | – |
| POST | `/api/login/` | Log in and set `access_token` and `refresh_token` cookies | – |
| POST | `/api/logout/` | Blacklist the refresh token and delete the cookies | ✔ |
| POST | `/api/token/refresh/` | Set a new `access_token` cookie using the refresh token | refresh cookie |

### Quizzes

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/quizzes/` | Create a quiz from a YouTube URL (`{"url": "..."}`) | ✔ |
| GET | `/api/quizzes/` | List all quizzes of the current user | ✔ |
| GET | `/api/quizzes/{id}/` | Get a single quiz with its questions | ✔ owner |
| PATCH | `/api/quizzes/{id}/` | Update `title` and/or `description` | ✔ owner |
| DELETE | `/api/quizzes/{id}/` | Delete a quiz and all its questions | ✔ owner |

Status codes: `400` invalid data or URL, `401` not authenticated,
`403` quiz belongs to another user, `404` quiz not found,
`500` quiz generation failed.

## How the quiz generation works

```
YouTube URL
   │  extract the video ID and build https://www.youtube.com/watch?v=<id>
   ▼
yt-dlp      → downloads only the audio track into a temporary folder
   ▼
Whisper     → transcribes the audio locally (model "base", needs FFmpeg)
   ▼
Gemini      → creates title, description and 10 questions as JSON
   ▼
Validation  → exactly 10 questions, 4 options each, answer is one of the options
   ▼
Database    → quiz and questions are saved in one transaction
```

The Gemini model is set in `GEMINI_MODEL_NAME` in `quiz_app/utils.py`.
If a model is overloaded, you can switch to another Flash model there.

## Project Structure

```
backend/
├── core/               # Django settings and main URLs
├── auth_app/
│   ├── api/            # serializers, views and urls for authentication
│   ├── authentication.py   # reads the JWT from the HTTP-only cookie
│   └── utils.py        # cookie and token helper functions
├── quiz_app/
│   ├── api/            # serializers, views, permissions and urls for quizzes
│   ├── admin.py        # admin panel for quizzes and questions
│   ├── models.py       # Quiz and Question models
│   └── utils.py        # yt-dlp, Whisper and Gemini pipeline
├── .env.example
├── manage.py
└── requirements.txt
```

## Notes

- The first quiz takes a bit longer because Whisper downloads its model (~140 MB).
- Whisper runs on the CPU, so short videos are recommended for testing.
- Cookies use `secure=False` for local development. Set it to `True`
  in `auth_app/utils.py` when running the backend over HTTPS.
