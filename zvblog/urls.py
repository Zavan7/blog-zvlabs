"""Rotas do projeto: admin, login social e blog.

English:
    Project routes: admin, social login and blog.
"""

from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Blog ZV Labs"
admin.site.site_title = "Blog ZV Labs"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("contas/", include("allauth.urls")),
    path("", include("blog.urls")),
]
