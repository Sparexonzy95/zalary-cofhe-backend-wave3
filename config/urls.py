from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.cofhe.urls")),
    path("api/v1/onboarding/", include("apps.onboarding.urls")),
]