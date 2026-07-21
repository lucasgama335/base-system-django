from django.urls import path
from .views import auth 

app_name = "accounts"

urlpatterns = [
    path("login/", auth.login_view, name="login"),
    path("logout/", auth.logout_view, name="logout"),
    # Reset Password URLS
    path(route="reset-password", view=auth.PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", auth.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", auth.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset_complete/done/", auth.PasswordResetCompleteView.as_view(), name="password_reset_complete")
]