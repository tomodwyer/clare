from django.urls import path

import views

urlpatterns = [
    path("", views.home, name="home"),
    path("<path:path>/", views.page, name="page"),
]
