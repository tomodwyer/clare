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
from django.urls import re_path
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
def page(request, path):
    if not path:
        path = "home"

    with open(f"pages/{path}.txt") as f:
        data = f.read()

    template_name = "page.html"
    ctx = {
        "page_id": path.replace("/", "-"),
        "sections": [],
    }

    for ix, section in enumerate(data.split("---")):
        section = section.strip()

        if ix == 0:
            page_metadata = load_yaml(section)
            if "template" in page_metadata:
                template_name = page_metadata["template"]
            ctx["title"] = page_metadata.get("title")
            ctx["subtitle"] = page_metadata.get("subtitle")
            if "main_image" in page_metadata:
                ctx["main_image"] = f"img/{page_metadata['main_image']}"
        else:
            section_metadata, section_data = section.split("\n\n", 1)
            section_metadata = load_yaml(section_metadata)
            section_type = section_metadata["type"]

            section_ctx = {
                "audio": audio_ctx,
                "concerts": concerts_ctx,
                "gallery": gallery_ctx,
                "modal-gallery": gallery_ctx,
                "project-listing": project_listing_ctx,
                "repertoire": repertoire_ctx,
                "sponsor-logos": sponsor_logos_ctx,
                "text": text_ctx,
                "video": video_ctx,
            }[section_type](section_data)

            section_ctx["template"] = f"components/{section_type}.html"
            section_ctx["subtitle"] = section_metadata.get("subtitle")
            section_ctx["header"] = load_markdown(section_metadata.get("header", ""))
            section_ctx["footer"] = load_markdown(section_metadata.get("footer", ""))

            ctx["sections"].append(section_ctx)

    return render(request, template_name, ctx)


def audio_ctx(data):
    audios = load_yaml(data)
    for audio in audios:
        audio["path"] = f"audio/{audio['path']}"
    return {"audios": audios}


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
        if base.endswith("-medium"):
            base = base.removesuffix("-medium")
        thumb_path = f"{base}-thumb{ext}"
        images.append(
            {
                "title": image.get("title"),
                "description": image.get("description", image.get("title")),
                "details": image.get("details", ""),
                "path": path,
                "thumb_path": thumb_path,
            }
        )
    return {"images": images}


def project_listing_ctx(data):
    items = []
    for item in load_yaml(data):
        items.append(
            {
                "title": item.get("title"),
                "page_path": item["page_path"] + "/",
                "image_path": f"img/{item['image_path']}",
                "details": load_markdown(item.get("details", "")),
            }
        )
    return {"items": items}


def repertoire_ctx(data):
    records = []
    last_composer = None
    for r in load_tsv(data):
        if last_composer is not None and r[0] == last_composer:
            records.append(["", r[1]])
        else:
            records.append(r)
        last_composer = r[0]
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
    re_path("(?P<path>.*/?)", page, name="page"),
]

# wsgi.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "application")
application = get_wsgi_application()


# manage.py
if __name__ == "__main__":
    execute_from_command_line(sys.argv)
