from django.urls import path
from .views import LoginWithClienteView, CreateUserView, MeClientsView
from .view_users import CreateUserMultiClienteView
from .views_membership import AddMembershipView

urlpatterns = [
    path("auth/novo_login/", LoginWithClienteView.as_view(), name="auth-login"),
    path("auth/users/", CreateUserView.as_view(), name="auth-create-user"),
    path("auth/me/clients/", MeClientsView.as_view(), name="me-clients"),
    path("auth/users/", CreateUserMultiClienteView.as_view(), name="auth-create-user-multi"),
    path("auth/users/<int:user_id>/memberships/", AddMembershipView.as_view(), name="auth-add-membership"),
]
