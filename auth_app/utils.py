"""Helper functions for handling the JWT auth cookies."""

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

COOKIE_SETTINGS = {"httponly": True, "secure": False, "samesite": "Lax"}


def set_access_cookie(response, access_token):
    """Store the access token in an HTTP-only cookie."""
    response.set_cookie("access_token", access_token, **COOKIE_SETTINGS)


def set_auth_cookies(response, refresh_token):
    """Store access and refresh token in HTTP-only cookies."""
    set_access_cookie(response, str(refresh_token.access_token))
    response.set_cookie("refresh_token", str(refresh_token), **COOKIE_SETTINGS)


def delete_auth_cookies(response):
    """Remove both auth cookies from the client."""
    response.delete_cookie("access_token", samesite="Lax")
    response.delete_cookie("refresh_token", samesite="Lax")


def blacklist_refresh_token(raw_token):
    """Put the given refresh token on the blacklist so it can't be used again."""
    if raw_token is None:
        return
    try:
        RefreshToken(raw_token).blacklist()
    except TokenError:
        pass


def get_user_data(user):
    """Return the public user data for the login response."""
    return {"id": user.id, "username": user.username, "email": user.email}
