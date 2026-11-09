from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticates requests via the JWT access token stored in an HTTP-only cookie."""

    def authenticate(self, request):
        """Return (user, token) if a valid access token cookie exists, otherwise None."""
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
