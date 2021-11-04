import csv

import tomli
from django.shortcuts import render
from django.utils.safestring import mark_safe
from markdown import markdown


def home(request):
    content = _load_markdown("pages/home.md")
    ctx = {"content": content}
    return render(request, "home.html", ctx)


def biography(request):
    content = _load_markdown("pages/biography.md")
    ctx = {"page_id": "biography", "content": content}
    return render(request, "biography.html", ctx)


def concerts(request):
    with open("pages/concerts.toml") as f:
        concerts = tomli.load(f)["concert"]
    for concert in concerts:
        if "summary" in concert:
            concert["summary"] = mark_safe(markdown(concert["summary"]))
        if "details" in concert:
            concert["details"] = [
                mark_safe(markdown(detail)) for detail in concert["details"]
            ]
    ctx = {"concerts": concerts}
    return render(request, "concerts.html", ctx)


def repertoire(request, category):
    records = []
    with open(f"pages/repertoire/{category}.tsv") as f:
        for r in csv.reader(f, delimiter="\t"):
            if records and r[0] == records[-1][0]:
                records.append(["", r[1]])
            else:
                records.append(r)
    ctx = {"records": records, "title": f"{category.title()} Repertoire"}
    return render(request, "repertoire.html", ctx)


def _load_markdown(path):
    with open(path) as f:
        md = f.read()
    raw_html = markdown(md)
    # There's probably a better way of doing this via a markdown extension...
    html = raw_html.replace("<p>!", '<p class="lead">')
    return mark_safe(html)
