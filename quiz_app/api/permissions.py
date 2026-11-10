from rest_framework.permissions import BasePermission


class IsQuizOwner(BasePermission):
    """Allows access only to the user who created the quiz."""

    def has_object_permission(self, request, view, obj):
        """Return True if the requesting user owns the quiz."""
        return obj.user == request.user
