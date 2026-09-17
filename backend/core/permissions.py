"""
Custom DRF permissions for QAIP.

All permissions enforce individual student ownership — no cross-student access.
"""
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Allow access only to the owner of an object.
    Expects the object to have a `student` attribute that links back to a
    StudentProfile, which has a `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Support objects owned via .student.user or directly via .user
        if hasattr(obj, 'student'):
            return obj.student.user == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsStudentOwner(BasePermission):
    """
    Allow access only when request.user owns the StudentProfile object.
    Used on StudentProfile views directly.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
