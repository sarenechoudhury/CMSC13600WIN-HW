import hashlib
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

import requests
from zoneinfo import ZoneInfo

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseNotAllowed,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
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

    try:
        total = float(n1) + float(n2)
    except ValueError:
        return HttpResponse("n1 and n2 must be numbers", status=400)

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
    except AttributeError:
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

    is_curator = is_curator_raw == "1"

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


def _visible_uploads_for_user(user):
    if user_is_curator(user):
        return Upload.objects.all().select_related(
            "uploader", "institution", "reporting_year"
        )
    return Upload.objects.filter(uploader=user).select_related(
        "uploader", "institution", "reporting_year"
    )


def uploads(request):
    if not request.user.is_authenticated:
        return HttpResponse("unauthorized", status=401)

    upload_list = _visible_uploads_for_user(request.user)

    context = {
        "uploads": upload_list,
    }
    return render(request, "uncommondata/uploads.html", context)


def show_uploads(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    return uploads(request)


@csrf_exempt
def upload_api(request):
    if not request.user.is_authenticated:
        return HttpResponse("unauthorized", status=401)

    if user_is_curator(request.user):
        return HttpResponse("forbidden", status=403)

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

    file_bytes = uploaded_file.read()
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    uploaded_file.seek(0)

    upload, created = Upload.objects.get_or_create(
        sha256=sha256,
        defaults={
            "uploader": request.user,
            "institution": institution,
            "reporting_year": reporting_year,
            "url": url if url else None,
            "uploaded_file": uploaded_file,
        },
    )

    if not created:
        return JsonResponse(
            {
                "status": "success",
                "id": upload.sha256,
                "message": "file already uploaded",
            },
            status=200,
        )

    return JsonResponse(
        {
            "status": "success",
            "id": upload.sha256,
        },
        status=201,
    )


def dump_uploads(request):
    if not request.user.is_authenticated:
        return HttpResponse("unauthorized", status=401)

    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    upload_qs = _visible_uploads_for_user(request.user)

    result = {}
    for upload in upload_qs:
        result[upload.sha256] = {
            "user": upload.uploader.username,
            "institution": upload.institution.name,
            "year": upload.reporting_year.label,
            "url": upload.url,
            "file": Path(upload.uploaded_file.name).name,
            "download_url": f"/app/api/download/{upload.sha256}/",
            "process_url": f"/app/api/process/{upload.sha256}/",
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


def download(request, id):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    if not request.user.is_authenticated:
        return HttpResponse("unauthorized", status=401)

    upload = get_object_or_404(
        _visible_uploads_for_user(request.user),
        sha256=id,
    )

    return FileResponse(
        upload.uploaded_file.open("rb"),
        as_attachment=True,
        filename=Path(upload.uploaded_file.name).name,
    )


def pdf_to_text(filename):
    """
    Run pdftotext on filename and return the path to the generated text file.
    """
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Input file not found: {filename}")

    output_filename = filename + ".txt"

    try:
        subprocess.run(
            ["pdftotext", "-layout", filename, output_filename],
            check=True,
        )
    except FileNotFoundError:
        raise RuntimeError("pdftotext is not installed")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"pdftotext failed with exit code {e.returncode}") from e

    return output_filename


def normalize_text(text):
    replacements = {
        "\u2019": "'",
        "\u2018": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
        "Ɵ": "ti",
        "Ʃ": "tt",
        "ﬁ": "fi",
        "ﬀ": "ff",
        "oīered": "offered",
        "admiƩed": "admitted",
        "submiƩed": "submitted",
        "ﬁrst": "first",
        "ﬁnancial": "financial",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[ \t]+", " ", text)
    return text


def _clean_number(value):
    if value is None:
        return None
    cleaned = value.replace(",", "").replace("$", "").strip()
    if cleaned in {"", "-", "--", "N/A", "n/a"}:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def _extract_first_number_after_label(text, labels):
    for label in labels:
        pattern = re.compile(
            rf"{re.escape(label)}[\s:\.\-]*\$?\s*([\d,]+)",
            re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            return _clean_number(match.group(1))

        looser_pattern = re.compile(
            rf"{re.escape(label)}.*?\$?\s*([\d,]+)",
            re.IGNORECASE | re.DOTALL,
        )
        match = looser_pattern.search(text)
        if match:
            return _clean_number(match.group(1))
    return None


def _extract_section_row_numbers(text, row_label):
    """
    For rows like:
    Total first-time, first-year (freshman) who applied: 14,533 13,945 0 0 28,478
    Return the first four numbers.
    """
    pattern = re.compile(
        rf"{re.escape(row_label)}.*?([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None
    return [
        _clean_number(match.group(1)),
        _clean_number(match.group(2)),
        _clean_number(match.group(3)),
        _clean_number(match.group(4)),
    ]


def _extract_c1_by_explicit_labels(text):
    data = {
        "men_applied": None,
        "women_applied": None,
        "another_gender_applied": None,
        "unknown_gender_applied": None,
        "men_admitted": None,
        "women_admitted": None,
        "another_gender_admitted": None,
        "unknown_gender_admitted": None,
    }

    explicit_patterns = {
        "men_applied": [
            "Total first-time, first-year men who applied",
        ],
        "women_applied": [
            "Total first-time, first-year women who applied",
        ],
        "another_gender_applied": [
            "Total first-time, first-year another gender who applied",
        ],
        "unknown_gender_applied": [
            "Total first-time, first-year unknown gender who applied",
        ],
        "men_admitted": [
            "Total first-time, first-year men who were admitted",
        ],
        "women_admitted": [
            "Total first-time, first-year women who were admitted",
        ],
        "another_gender_admitted": [
            "Total first-time, first-year another gender who were admitted",
        ],
        "unknown_gender_admitted": [
            "Total first-time, first-year unknown gender who were admitted",
        ],
    }

    for key, labels in explicit_patterns.items():
        data[key] = _extract_first_number_after_label(text, labels)

    return data


def _extract_c1_by_row_table(text):
    data = {
        "men_applied": None,
        "women_applied": None,
        "another_gender_applied": None,
        "unknown_gender_applied": None,
        "men_admitted": None,
        "women_admitted": None,
        "another_gender_admitted": None,
        "unknown_gender_admitted": None,
    }

    applied = _extract_section_row_numbers(
        text,
        "Total first-time, first-year (freshman) who applied",
    )
    if applied:
        data["men_applied"] = applied[0]
        data["women_applied"] = applied[1]
        data["another_gender_applied"] = applied[2]
        data["unknown_gender_applied"] = applied[3]

    admitted = _extract_section_row_numbers(
        text,
        "Total first-time, first-year (freshman) who were admitted",
    )
    if admitted:
        data["men_admitted"] = admitted[0]
        data["women_admitted"] = admitted[1]
        data["another_gender_admitted"] = admitted[2]
        data["unknown_gender_admitted"] = admitted[3]

    return data


def _merge_first_non_null(base, extra):
    for key, value in extra.items():
        if base.get(key) is None and value is not None:
            base[key] = value
    return base


def extract_cds_fields(text):
    text = normalize_text(text)

    data = {
        "tuition_undergraduates": None,
        "required_fees_undergraduates": None,
        "food_and_housing_on_campus_undergraduates": None,
        "housing_only_on_campus_undergraduates": None,
        "food_only_on_campus_meal_plan_undergraduates": None,
        "degree_seeking_undergraduate_students": None,
        "applied_for_need_based_financial_aid": None,
        "determined_to_have_financial_need": None,
        "awarded_any_financial_aid": None,
        "average_financial_aid_package": None,
        "men_applied": None,
        "women_applied": None,
        "another_gender_applied": None,
        "unknown_gender_applied": None,
        "men_admitted": None,
        "women_admitted": None,
        "another_gender_admitted": None,
        "unknown_gender_admitted": None,
    }

    data["tuition_undergraduates"] = _extract_first_number_after_label(
        text,
        [
            "Tuition (Undergraduates)",
            "Tuition Undergraduates",
            "Tuition",
        ],
    )

    data["required_fees_undergraduates"] = _extract_first_number_after_label(
        text,
        [
            "Required Fees: (Undergraduates)",
            "Required Fees (Undergraduates)",
            "Required Fees",
        ],
    )

    data["food_and_housing_on_campus_undergraduates"] = _extract_first_number_after_label(
        text,
        [
            "Food and housing (on-campus): (Undergraduates)",
            "Food and housing (on-campus) (Undergraduates)",
            "Food and housing (on-campus)",
        ],
    )

    data["housing_only_on_campus_undergraduates"] = _extract_first_number_after_label(
        text,
        [
            "Housing Only (on-campus): (Undergraduates)",
            "Housing Only (on-campus) (Undergraduates)",
            "Housing Only (on-campus)",
        ],
    )

    data["food_only_on_campus_meal_plan_undergraduates"] = _extract_first_number_after_label(
        text,
        [
            "Food Only (on-campus meal plan): (Undergraudates)",
            "Food Only (on-campus meal plan): (Undergraduates)",
            "Food Only (on-campus meal plan) (Undergraduates)",
            "Food Only (on-campus meal plan)",
        ],
    )

    data["degree_seeking_undergraduate_students"] = _extract_first_number_after_label(
        text,
        [
            "A. Number of degree-seeking undergraduate students",
            "Number of degree-seeking undergraduate students",
        ],
    )

    data["applied_for_need_based_financial_aid"] = _extract_first_number_after_label(
        text,
        [
            "B. Number of students in line a who applied for need-based financial aid",
            "B. Number of students in line a who applied for need based financial aid",
            "Number of students in line a who applied for need-based financial aid",
        ],
    )

    data["determined_to_have_financial_need"] = _extract_first_number_after_label(
        text,
        [
            "C. Number of students in line b who were determined to have financial need",
            "Number of students in line b who were determined to have financial need",
        ],
    )

    data["awarded_any_financial_aid"] = _extract_first_number_after_label(
        text,
        [
            "D. Number of students in line c who were awarded any financial aid",
            "Number of students in line c who were awarded any financial aid",
        ],
    )

    data["average_financial_aid_package"] = _extract_first_number_after_label(
        text,
        [
            "J. The average financial aid package of those in line d",
            "The average financial aid package of those in line d",
        ],
    )

    explicit_c1 = _extract_c1_by_explicit_labels(text)
    row_c1 = _extract_c1_by_row_table(text)

    data = _merge_first_non_null(data, explicit_c1)
    data = _merge_first_non_null(data, row_c1)

    return data


def process(request, id):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    if not request.user.is_authenticated:
        return HttpResponse("unauthorized", status=401)

    upload = get_object_or_404(
        _visible_uploads_for_user(request.user),
        sha256=id,
    )

    filepath = upload.uploaded_file.path
    lower_path = filepath.lower()

    try:
        if lower_path.endswith(".pdf"):
            text_path = pdf_to_text(filepath)
            with open(text_path, "r", encoding="utf-8", errors="ignore") as handle:
                text = handle.read()

        elif lower_path.endswith(".txt"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as handle:
                text = handle.read()

        else:
            return JsonResponse(
                {"error": "unsupported file type; please upload a PDF or TXT file"},
                status=400,
            )

    except Exception as exc:
        return JsonResponse(
            {"error": f"could not process file: {exc}"},
            status=400,
        )

    extracted = extract_cds_fields(text)
    return JsonResponse(extracted, status=200)


def knockknock(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    topic = request.GET.get("topic", "orange").strip()
    topic = " ".join(topic.split()[:5])

    if not topic:
        topic = "orange"

    fallback_joke = (
        "Knock knock\n"
        "Who's there\n"
        f"{topic}\n"
        f"{topic} who\n"
        f"{topic.capitalize()} you glad this endpoint has a fallback joke"
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
        joke = joke.replace("’", "'").replace("‘", "'")
        return HttpResponse(joke, content_type="text/plain", status=200)
    except Exception:
        return HttpResponse(fallback_joke, content_type="text/plain", status=200)
