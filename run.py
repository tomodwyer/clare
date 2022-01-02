#!/usr/bin/env python
import csv
import os
import re
import shutil
from argparse import ArgumentParser
from pathlib import Path

import tomli
import yaml
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application
from django.shortcuts import render
from django.urls import path
from django.utils.safestring import mark_safe
from markdown import markdown

MODULE_NAME = Path(__file__).with_suffix("").name
os.environ.setdefault("DJANGO_SETTINGS_MODULE", MODULE_NAME)

PAGES = "pages"
STATIC = "static"
TEMPLATES = "templates"

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "not-secret"
DEBUG = True
ALLOWED_HOSTS = ["*"]

ROOT_URLCONF = MODULE_NAME
WSGI_APPLICATION = f"{MODULE_NAME}.application"

INSTALLED_APPS = [
    "django.contrib.staticfiles",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / TEMPLATES],
    },
]

STATIC_URL = f"/{STATIC}/"
STATICFILES_DIRS = [BASE_DIR / STATIC]


def page(request, path):
    if not path:
        path = "home"

    with open(f"{PAGES}/{path}.txt") as f:
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
            ctx["title"] = load_markdown(page_metadata.get("title"), False)
            ctx["subtitle"] = load_markdown(page_metadata.get("subtitle"), False)
            if "main_image" in page_metadata:
                ctx["main_image"] = f"img/{page_metadata['main_image']}"
        else:
            try:
                section_metadata, section_data = section.split("\n\n", 1)
            except ValueError:
                section_metadata, section_data = section, ""
            section_ctx = load_yaml(section_metadata)
            section_type = section_ctx["type"]

            section_ctx["section_id"] = f"section-{ix}"
            if "template" not in section_ctx:
                section_ctx["template"] = f"components/{section_type}.html"
            if "header" in section_ctx:
                section_ctx["header"] = load_markdown(section_ctx["header"])
            if "footer" in section_ctx:
                section_ctx["footer"] = load_markdown(section_ctx["footer"])
            section_ctx["subtitle"] = load_markdown(section_ctx.get("subtitle"), False)
            section_ctx["id"] = section_ctx.get("id") or slugify(
                section_ctx["subtitle"]
            )

            extra_ctx_fn = {
                "audio": audio_ctx,
                "concerts": concerts_ctx,
                "custom": custom_ctx,
                "gallery": gallery_ctx,
                "modal-gallery": gallery_ctx,
                "project-listing": project_listing_ctx,
                "repertoire": repertoire_ctx,
                "review": review_ctx,
                "sponsor-logos": sponsor_logos_ctx,
                "text": text_ctx,
                "video": video_ctx,
            }[section_type]
            section_ctx.update(extra_ctx_fn(section_ctx, section_data))

            ctx["sections"].append(section_ctx)

    return render(request, template_name, ctx)


def audio_ctx(metadata, data):
    audios = load_yaml(data)
    for audio in audios:
        audio["path"] = f"audio/{audio['path']}"
        audio["description"] = load_markdown(audio.get("description"))
    return {"audios": audios}


def concerts_ctx(metadata, data):
    concerts = load_tomli(data)["concert"]
    for concert in concerts:
        if "summary" in concert:
            concert["summary"] = load_markdown(concert["summary"])
        if "details" in concert:
            concert["details"] = [
                load_markdown(detail) for detail in concert["details"]
            ]
        if "repertoire" in concert:
            concert["repertoire"] = [
                [load_markdown(item, False) for item in repertoire_item]
                for repertoire_item in concert["repertoire"]
            ]
    return {"concerts": concerts}


def custom_ctx(metadata, data):
    return {}


def gallery_ctx(metadata, data):
    images = []
    for image in load_yaml(data):
        path = f"img/{image['path']}"
        base, ext = os.path.splitext(path)
        if base.endswith("-medium"):
            base = base[: -len("-medium")]
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


def project_listing_ctx(metadata, data):
    items = []
    for item in load_yaml(data):
        items.append(
            {
                "title": load_markdown(item["title"]),
                "page_path": item["page_path"] + "/",
                "image_path": f"img/{item['image_path']}",
                "details": load_markdown(item.get("details", "")),
            }
        )
    return {"items": items}


def repertoire_ctx(metadata, data):
    records = []
    last_composer = None
    for r in load_tsv(data):
        r[1] = load_markdown(r[1], False)
        if last_composer is not None and r[0] == last_composer:
            records.append(["", r[1]])
        else:
            records.append(r)
        last_composer = r[0]
    return {"records": records}


def review_ctx(metadata, data):
    metadata["review"] = load_markdown(data)
    return metadata


def sponsor_logos_ctx(metadata, data):
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


def text_ctx(metadata, data):
    return {"text": load_markdown(data)}


def video_ctx(metadata, data):
    return {"videos": load_yaml(data)}


def load_markdown(s, in_para=True):
    if s is None:
        return

    html = markdown(s)
    # There's probably a better way of doing this via a markdown extension...
    html = html.replace("<p>!", '<p class="lead">')
    html = html.replace('<a href="http', '<a target="_blank" href="http')
    if html and not in_para:
        assert html[:3] == "<p>" and html[-4:] == "</p>", html
        html = html[3:-4]
    return mark_safe(html)


def load_tomli(s):
    return tomli.loads(s)


def load_tsv(s):
    return list(csv.reader(s.splitlines(), delimiter="\t"))


def load_yaml(s):
    return yaml.load(s, yaml.SafeLoader) or {}


def slugify(value):
    if value is None:
        return
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


urlpatterns = [
    path("", page, {"path": ""}),
    path("<path:path>/", page),
]

application = get_wsgi_application()


def build(base_output_dir):
    assert base_output_dir.name not in [PAGES, STATIC, TEMPLATES]
    shutil.rmtree(base_output_dir, ignore_errors=True)
    base_output_dir.mkdir()
    shutil.copytree(STATIC, base_output_dir / STATIC)
    for root, dirs, files in os.walk(PAGES):
        for file in files:
            if not file.endswith(".txt"):
                continue
            path = os.path.join(root, file)[len(PAGES) + 1 : -4]
            if path == "home":
                path = ""
            output_dir = base_output_dir / path
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "index.html"
            print(output_path)
            output_path.write_bytes(page(None, path).content)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.set_defaults(which="print_help")
    subparsers = parser.add_subparsers()
    serve_parser = subparsers.add_parser("serve", help="Serve site")
    serve_parser.set_defaults(which="serve")
    serve_parser.add_argument("--port", type=int, default=8000)
    build_parser = subparsers.add_parser("build", help="Build site")
    build_parser.set_defaults(which="build")
    build_parser.add_argument("--output-dir", type=Path, default="output")
    options = parser.parse_args()
    if options.which == "serve":
        execute_from_command_line(["manage.py", "runserver", str(options.port)])
    elif options.which == "build":
        build(options.output_dir)
    else:
        parser.print_help()
