#!/usr/bin/env python
import csv
import os
import sys
from pathlib import Path

import tomli
import yaml
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application
from django.shortcuts import render
from django.urls import path
from django.utils.safestring import mark_safe
from markdown import markdown

# settings.py
BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "not-secret"
DEBUG = True
ALLOWED_HOSTS = ["*"]

ROOT_URLCONF = "application"
WSGI_APPLICATION = "application.application"

INSTALLED_APPS = [
    "django.contrib.staticfiles",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
    },
]

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]


# views.py
def home(request):
    with open("pages/home.md") as f:
        content = load_markdown(f.read())
    ctx = {"content": content}
    return render(request, "home.html", ctx)


def page(request, path):
    with open(f"pages/{path}.txt") as f:
        data = f.read()

    ctx = {"sections": []}

    for ix, section in enumerate(data.split("---")):
        section = section.strip()

        if ix == 0:
            page_metadata = load_yaml(section)
            ctx["title"] = page_metadata.get("title")
            main_image = page_metadata.get("main_image")
            if main_image is not None:
                ctx["main_image"] = f"img/{main_image}"
        else:
            section_metadata, section_data = section.split("\n\n", 1)
            section_metadata = load_yaml(section_metadata)
            section_type = section_metadata["type"]

            section_ctx = {
                "concerts": concerts_ctx,
                "gallery": gallery_ctx,
                "repertoire": repertoire_ctx,
                "sponsor-logos": sponsor_logos_ctx,
                "text": text_ctx,
                "video": video_ctx,
            }[section_type](section_data)

            section_ctx["template"] = f"_{section_type}.html"
            if "subtitle" in section_metadata:
                section_ctx["subtitle"] = section_metadata["subtitle"]

            ctx["sections"].append(section_ctx)

    return render(request, "page.html", ctx)


def concerts_ctx(data):
    concerts = load_tomli(data)["concert"]
    for concert in concerts:
        if "summary" in concert:
            concert["summary"] = mark_safe(markdown(concert["summary"]))
        if "details" in concert:
            concert["details"] = [
                mark_safe(markdown(detail)) for detail in concert["details"]
            ]
    return {"concerts": concerts}


def gallery_ctx(data):
    images = []
    for image in load_yaml(data):
        path = f"img/{image['path']}"
        base, ext = os.path.splitext(path)
        thumb_path = f"{base}-thumb{ext}"
        images.append(
            {
                "title": image["title"],
                "description": image.get("description", image["title"]),
                "details": image.get("details", ""),
                "path": path,
                "thumb_path": thumb_path,
            }
        )
    return {"images": images}


def repertoire_ctx(data):
    records = []
    for r in load_tsv(data):
        if records and r[0] == records[-1][0]:
            records.append(["", r[1]])
        else:
            records.append(r)
    return {"records": records}


def sponsor_logos_ctx(data):
    logos = []
    for logo in load_yaml(data):
        path = f"img/logos/{logo['path']}"
        logos.append(
            {
                "name": logo["name"],
                "path": path,
                "url": logo["url"],
            }
        )
    return {"logos": logos}


def text_ctx(data):
    return {"text": load_markdown(data)}


def video_ctx(data):
    return {"videos": load_yaml(data)}


def load_markdown(s):
    raw_html = markdown(s)
    # There's probably a better way of doing this via a markdown extension...
    html = raw_html.replace("<p>!", '<p class="lead">')
    return mark_safe(html)


def load_tomli(s):
    return tomli.loads(s)


def load_tsv(s):
    return list(csv.reader(s.splitlines(), delimiter="\t"))


def load_yaml(s):
    return yaml.load(s, yaml.SafeLoader) or {}


# urls.py
urlpatterns = [
    path("", home, name="home"),
    path("<path:path>/", page, name="page"),
]

# wsgi.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "application")
application = get_wsgi_application()


# manage.py
if __name__ == "__main__":
    execute_from_command_line(sys.argv)