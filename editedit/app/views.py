from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.contrib.auth.models import User
from .models import PageRevision, Page, UserProfile
from datetime import datetime
from zoneinfo import ZoneInfo


''' Views to process POST requests to update
wikipedia-like content in database '''

def index(request):
    current_time = datetime.now(ZoneInfo("America/Chicago")).strftime("%H:%M")
    context = {
        "current_time": current_time,
    }
    return render(request, 'app/index.html', context)


def new_user_form(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    return render(request, 'app/new.html')


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
        password=password
    )

    UserProfile.objects.create(
        user=user,
        is_curator=is_curator
    )

    login(request, user)

    return HttpResponse("success", status=201)


@csrf_exempt
def editpage(request):
    print("KEYS", request.POST.keys())
    content = request.POST['content']
    page_title = request.POST["page"]

    print("PAGE", page_title)
    print("CONTENT:", content)

    # If page isn't in Page table, add it first
    page_obj, created = Page.objects.get_or_create(title=page_title)

    # Add row to PageRevision table
    page_revision = PageRevision(
        page=page_obj,
        content=content,
        edited_at=datetime.now(),
        editor=request.user if request.user.is_authenticated else None
    )
    page_revision.save()

    return HttpResponse("")

'''  Sample command-line POST request: 
  curl -X POST http://localhost:8000/app/editpage \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "page=default+page&content=This+is+some+content+MORE"
'''

