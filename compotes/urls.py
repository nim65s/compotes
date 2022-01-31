"""compotes URL Configuration."""

from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls),
    path("", views.UserListView.as_view(), name="home"),
    path("debt/add", views.DebtCreateView.as_view(), name="debt_create"),
    path("debt/<int:pk>", views.DebtDetailView.as_view(), name="debt_detail"),
    path("debt/<int:pk>/update", views.DebtUpdateView.as_view(), name="debt_update"),
    path("debt/<int:pk>/parts", views.PartsUpdateView.as_view(), name="parts_update"),
]
