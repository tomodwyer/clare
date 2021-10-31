from django.shortcuts import render
from django.utils.safestring import mark_safe
from markdown import markdown


def home(request):
    with open("pages/home.md") as f:
        news = mark_safe(markdown(f.read()))
    ctx = {"news": news}
    return render("request", "home.html", ctx)


def biography(request):
    with open("pages/biography.md") as f:
        content = mark_safe(markdown(f.read()))
    ctx = {"page_id": "biography", "content": content}
    return render("request", "page.html", ctx)
