from django.urls import path

import views

urlpatterns = [
    path("", views.home, name="home"),
    path("biography/", views.biography, name="biography"),
    path("concerts/", views.concerts, name="concerts"),
    path("repertoire/<category>/", views.repertoire, name="repertoire"),
    path("<path:path>/", views.page, name="page"),
]
