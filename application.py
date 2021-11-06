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
        content = _load_markdown(f.read())
    ctx = {"content": content}
    return render(request, "home.html", ctx)


def page(request, path):
    with open(f"pages/{path}.txt") as f:
        data = f.read()

    ctx = {"sections": []}

    for ix, section in enumerate(data.split("---")):
        section = section.strip()

        if ix == 0:
            page_metadata = _load_yaml(section)
            ctx["title"] = page_metadata.get("title")
            main_image = page_metadata.get("main_image")
            if main_image is not None:
                ctx["main_image"] = f"img/{main_image}"
        else:
            section_metadata, section_data = section.split("\n\n", 1)
            section_metadata = _load_yaml(section_metadata)
            section_type = section_metadata["type"]
            section_ctx = {"template": f"_{section_type}.html"}

            if "subtitle" in section_metadata:
                section_ctx["subtitle"] = section_metadata["subtitle"]

            if section_type == "text":
                section_ctx["text"] = _load_markdown(section_data)
            elif section_type == "video":
                section_ctx["videos"] = _load_yaml(section_data)
            elif section_type == "gallery":
                section_ctx["images"] = []
                for image in _load_yaml(section_data):
                    path = f"img/{image['path']}"
                    base, ext = os.path.splitext(path)
                    thumb_path = f"{base}-thumb{ext}"
                    section_ctx["images"].append(
                        {
                            "title": image["title"],
                            "description": image.get("description", image["title"]),
                            "details": image.get("details", ""),
                            "path": path,
                            "thumb_path": thumb_path,
                        }
                    )
            elif section_type == "sponsor-logos":
                section_ctx["logos"] = []
                for logo in _load_yaml(section_data):
                    path = f"img/logos/{logo['path']}"
                    section_ctx["logos"].append(
                        {
                            "name": logo["name"],
                            "path": path,
                            "url": logo["url"],
                        }
                    )
            elif section_type == "concerts":
                concerts = _load_tomli(section_data)["concert"]
                for concert in concerts:
                    if "summary" in concert:
                        concert["summary"] = mark_safe(markdown(concert["summary"]))
                    if "details" in concert:
                        concert["details"] = [
                            mark_safe(markdown(detail)) for detail in concert["details"]
                        ]
                section_ctx["concerts"] = concerts
            elif section_type == "repertoire":
                records = []
                for r in csv.reader(section_data.splitlines(), delimiter="\t"):
                    if records and r[0] == records[-1][0]:
                        records.append(["", r[1]])
                    else:
                        records.append(r)
                section_ctx["records"] = records

            ctx["sections"].append(section_ctx)

    return render(request, "page.html", ctx)


def _load_tomli(s):
    return tomli.loads(s)


def _load_yaml(s):
    return yaml.load(s, yaml.SafeLoader) or {}


def _load_markdown(s):
    raw_html = markdown(s)
    # There's probably a better way of doing this via a markdown extension...
    html = raw_html.replace("<p>!", '<p class="lead">')
    return mark_safe(html)


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
