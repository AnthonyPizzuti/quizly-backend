from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.utils import (
    blacklist_refresh_token,
    delete_auth_cookies,
    get_user_data,
    set_access_cookie,
    set_auth_cookies,
)
from .serializers import RegistrationSerializer


class RegistrationView(APIView):
    """Registers a new user."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """Validate the data and save the new user."""
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(
            {"detail": "User created successfully!"}, status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """Logs in a user and sets the JWT cookies."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """Check the credentials and return the user data with auth cookies."""
        user = authenticate(
            username=request.data.get("username"),
            password=request.data.get("password"),
        )
        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        response = Response(
            {"detail": "Login successfully!", "user": get_user_data(user)}
        )
        set_auth_cookies(response, RefreshToken.for_user(user))
        return response


class LogoutView(APIView):
    """Logs out the user, blacklists the refresh token and deletes the cookies."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Invalidate the refresh token and remove both auth cookies."""
        blacklist_refresh_token(request.COOKIES.get("refresh_token"))
        response = Response(
            {
                "detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."
            }
        )
        delete_auth_cookies(response)
        return response


class CookieTokenRefreshView(APIView):
    """Creates a new access token using the refresh token cookie."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """Validate the refresh token and set a new access token cookie."""
        raw_token = request.COOKIES.get("refresh_token")
        if raw_token is None:
            return Response(
                {"detail": "Refresh token not found."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            refresh_token = RefreshToken(raw_token)
        except TokenError:
            return Response(
                {"detail": "Refresh token invalid."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        response = Response({"detail": "Token refreshed"})
        set_access_cookie(response, str(refresh_token.access_token))
        return response
