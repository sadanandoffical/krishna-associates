from django.urls import path

from .views import (
    AdminCreateAssociateView,
    AdminLoginView,
    AssociateChangePasswordView,
    AssociateLoginView,
    AssociateProfileView,
    CurrentUserView,
    LogoutView,
    AdminAssociateDetailView,
    AdminAssociateStatusView,
    AdminAssociateResetPasswordView
)


urlpatterns = [
    path(
        "login/associate/",
        AssociateLoginView.as_view(),
        name="associate-login",
    ),

    path(
        "login/admin/",
        AdminLoginView.as_view(),
        name="admin-login",
    ),

    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),

    path(
        "me/",
        CurrentUserView.as_view(),
        name="current-user",
    ),

    path(
        "associate/profile/",
        AssociateProfileView.as_view(),
        name="associate-profile",
    ),

    path(
        "associate/password/",
        AssociateChangePasswordView.as_view(),
        name="associate-change-password",
    ),

    path(
        "admin/associates/",
        AdminCreateAssociateView.as_view(),
        name="admin-create-associate",
    ),
    path(
        "admin/associates/<str:associate_id>/",
        AdminAssociateDetailView.as_view(),
        name="admin-associate-detail",
    ),
    path(
        "admin/associates/<str:associate_id>/status/",
        AdminAssociateStatusView.as_view(),
        name="admin-associate-status",
    ),
    path(
        "admin/associates/<str:associate_id>/reset-password/",
        AdminAssociateResetPasswordView.as_view(),
        name="admin-associate-reset-password",
    ),
]