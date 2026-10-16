"""Rotas do app blog.

English:
    Blog app routes.
"""

from django.urls import path

from blog import views

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("posts/<slug:slug>/", views.post_detail, name="post_detail"),
    path(
        "posts/<slug:slug>/comentar/",
        views.comment_create,
        name="comment_create",
    ),
    path("inscricao/", views.subscribe, name="subscribe"),
    path(
        "inscricao/cancelar/<uuid:token>/",
        views.unsubscribe,
        name="unsubscribe",
    ),
]
