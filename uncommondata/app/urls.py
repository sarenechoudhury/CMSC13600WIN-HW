from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("index.html", views.index, name="index_html"),

    path("app/time", views.time_endpoint, name="time_endpoint"),
    path("app/sum", views.sum_endpoint, name="sum_endpoint"),

    path("app/new/", views.new_user_form, name="new_user_form"),
    path("app/api/createUser/", views.create_user, name="create_user"),

    path("app/uploads/", views.uploads, name="uploads"),
    path("app/show-uploads/", views.show_uploads, name="show_uploads"),

    path("app/api/upload/", views.upload_api, name="upload_api"),
    path("app/api/dump-uploads/", views.dump_uploads, name="dump_uploads"),
    path("app/api/dump-data/", views.dump_data, name="dump_data"),
    path("app/api/download/<str:id>/", views.download, name="download"),
    path("app/api/process/<str:id>/", views.process, name="process"),

    path("app/api/knockknock/", views.knockknock, name="knockknock"),
]