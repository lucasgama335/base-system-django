from django.urls import path

from .views import auth, profile, two_factor

app_name = "accounts"

urlpatterns = [
    path("login/", auth.login_view, name="login"),
    path("logout/", auth.logout_view, name="logout"),
    #Two-factor authentication
    path('2fa/setup/', two_factor.setup_2fa_view, name='2fa_setup'),
    path('2fa/verify/', two_factor.verify_2fa_view, name='2fa_verify'),
    path('2fa/switch/', two_factor.switch_2fa_view, name='switch_2fa'),
    # Reset Password URLS
    path(route="reset-password", view=auth.PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", auth.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", auth.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset_complete/done/", auth.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

    # Profile Routes
    path("profile/", profile.personal_data, name="profile")
]