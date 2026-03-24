from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import os

import requests

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import UserProfile, Upload, Institution, ReportingYear


def get_current_time_string():
    return datetime.now(ZoneInfo("America/Chicago")).strftime("%H:%M")


def index(request):
    context = {
        "current_time": get_current_time_string(),
    }
    return render(request, "uncommondata/index.html", context)


def time_endpoint(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    return HttpResponse(get_current_time_string())


def sum_endpoint(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    n1 = request.GET.get("n1")
    n2 = request.GET.get("n2")

    if n1 is None or n2 is None:
        return HttpResponse("missing n1 or n2", status=400)

    total = float(n1) + float(n2)

    if total.is_integer():
        return HttpResponse(str(int(total)))
    return HttpResponse(str(total))


def user_is_curator(user):
    if not user.is_authenticated:
        return False
    try:
        return user.profile.is_curator
    except UserProfile.DoesNotExist:
        return False


@csrf_exempt
def new_user_form(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    return render(request, "uncommondata/new.html")


@csrf_exempt
def create_user(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    email = request.POST.get("email")
    username = request.POST.get("user_name")
    password = request.POST.get("password")
    is_curator_raw = request.POST.get("is_curator")

    if email is None or username is None or password is None or is_curator_raw is None:
        return HttpResponse("missing required fields", status=400)

    if User.objects.filter(email=email).exists():
        return HttpResponse(f"email {email} already in use", status=400)

    is_curator = (is_curator_raw == "1")

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )

    UserProfile.objects.create(
        user=user,
        is_curator=is_curator,
    )

    login(request, user)
    return HttpResponse("success", status=201)


def uploads(request):
    if not request.user.is_authenticated:
        return HttpResponse("unauthorized", status=401)

    if user_is_curator(request.user):
        return HttpResponse("forbidden", status=403)

    upload_list = Upload.objects.filter(uploader=request.user).select_related(
        "uploader", "institution", "reporting_year"
    )

    context = {
        "uploads": upload_list,
    }
    return render(request, "uncommondata/uploads.html", context)


@csrf_exempt
def upload_api(request):
    if not request.user.is_authenticated:
        return HttpResponse("unauthorized", status=401)

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    institution_name = request.POST.get("institution")
    year_label = request.POST.get("year")
    url = request.POST.get("url")
    uploaded_file = request.FILES.get("file")

    if institution_name is None or year_label is None or uploaded_file is None:
        return HttpResponse("missing required fields", status=400)

    institution, _ = Institution.objects.get_or_create(name=institution_name)
    reporting_year, _ = ReportingYear.objects.get_or_create(label=year_label)

    Upload.objects.create(
        uploader=request.user,
        institution=institution,
        reporting_year=reporting_year,
        url=url if url else None,
        uploaded_file=uploaded_file,
    )

    return HttpResponse("success", status=201)


def dump_uploads(request):
    if not request.user.is_authenticated:
        return HttpResponse("unauthorized", status=401)

    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    if user_is_curator(request.user):
        upload_qs = Upload.objects.all().select_related(
            "uploader", "institution", "reporting_year"
        )
    else:
        upload_qs = Upload.objects.filter(uploader=request.user).select_related(
            "uploader", "institution", "reporting_year"
        )

    result = {}
    for upload in upload_qs:
        result[str(upload.id)] = {
            "user": upload.uploader.username,
            "institution": upload.institution.name,
            "year": upload.reporting_year.label,
            "url": upload.url,
            "file": Path(upload.uploaded_file.name).name,
        }

    return JsonResponse(result, status=200)


def dump_data(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    if not request.user.is_authenticated:
        return HttpResponse("unauthorized", status=401)

    if not user_is_curator(request.user):
        return HttpResponse("forbidden", status=403)

    return HttpResponse("curator access granted", status=200)


def knockknock(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    topic = request.GET.get("topic", "orange").strip()
    topic = " ".join(topic.split()[:5])

    if not topic:
        topic = "orange"

    fallback_joke = (
        "Knock knock.\n"
        "Who's there?\n"
        f"{topic}.\n"
        f"{topic} who?\n"
        f"{topic.capitalize()} you glad this endpoint has a fallback joke?"
    )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return HttpResponse(fallback_joke, content_type="text/plain", status=200)

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "Return only a short knock-knock joke in plain text.",
                    },
                    {
                        "role": "user",
                        "content": f"Write a knock-knock joke about {topic}. Include the topic word or a close pun on it.",
                    },
                ],
                "max_tokens": 120,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        joke = data["choices"][0]["message"]["content"].strip()
        return HttpResponse(joke, content_type="text/plain", status=200)
    except Exception:
        return HttpResponse(fallback_joke, content_type="text/plain", status=200)
