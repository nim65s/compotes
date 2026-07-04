"""compotes URL Configuration."""

from django.contrib import admin
from django.urls import include, path

from . import views

app_name = "compotes"
urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", views.UserListView.as_view(), name="home"),
    path("user/<slug:slug>", views.UserDetailView.as_view(), name="user_detail"),
    path("events", views.EventListView.as_view(), name="event_list"),
    path("event/add", views.EventCreateView.as_view(), name="event_create"),
    path("event/<slug:slug>", views.EventDetailView.as_view(), name="event_detail"),
    path(
        "event/<slug:slug>/update",
        views.EventUpdateView.as_view(),
        name="event_update",
    ),
    path(
        "event/<slug:slug>/close",
        views.EventCloseView.as_view(),
        name="event_close",
    ),
    path(
        "event/<slug:slug>/reopen",
        views.EventReopenView.as_view(),
        name="event_reopen",
    ),
    path("debts", views.DebtListView.as_view(), name="debt_list"),
    path("debt/add", views.DebtCreateView.as_view(), name="debt_create"),
    path("debt/<int:pk>", views.DebtDetailView.as_view(), name="debt_detail"),
    path("debt/<int:pk>/update", views.DebtUpdateView.as_view(), name="debt_update"),
    path("debt/<int:pk>/part", views.PartCreateView.as_view(), name="part_create"),
    path("part/<int:pk>", views.PartUpdateView.as_view(), name="part_update"),
    path("part/<int:pk>/delete", views.PartDeleteView.as_view(), name="part_delete"),
    path("pools", views.PoolListView.as_view(), name="pool_list"),
    path("pool/add", views.PoolCreateView.as_view(), name="pool_create"),
    path("pool/<slug:slug>", views.PoolDetailView.as_view(), name="pool_detail"),
    path("pool/<slug:slug>/update", views.PoolUpdateView.as_view(), name="pool_update"),
    path(
        "pool/<slug:slug>/share",
        views.ShareUpdateView.as_view(),
        name="share_update",
    ),
]
