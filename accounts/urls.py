from django.urls import path
from .views import LoginWithClienteView

urlpatterns = [
    path("auth/login/", LoginWithClienteView.as_view(), name="auth-login"),
]
