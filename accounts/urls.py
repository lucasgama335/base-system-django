from django.urls import path
from .views import auth 

app_name = "accounts"

urlpatterns = [
    path("login/", auth.login_view, name="login"),
    path("register/", auth.register_view, name="register"),
    path("recovery-password/", auth.password_recovery_view, name="recovery_password"),
    path("logout/", auth.logout_view, name="logout")
]