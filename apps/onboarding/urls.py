from django.urls import path

from apps.onboarding import views

urlpatterns = [
    path("auth/nonce/", views.auth_nonce),
    path("auth/verify/", views.auth_verify),
    path("auth/logout/", views.logout),

    path("profile/", views.profile_me),
    path("profile/employer/", views.employer_profile_update),
    path("profile/employee/", views.employee_profile_update),
    path("profile/employee/private-access/", views.employee_private_access_enabled),

    path("email/request-code/", views.email_request_code),
    path("email/verify/", views.email_verify),
]
