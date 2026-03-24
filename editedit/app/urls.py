from django.urls import path

from . import views

urlpatterns = [
    path('editpage', views.editpage, name='editpage'),
    path('', views.index, name='index'),
    path("index.html", views.index, name="index_html"),
    path("app/new/", views.new_user_form, name="new_user_form"),
    path("app/api/createUser/", views.create_user, name="create_user"),
    path("app/editpage", views.editpage, name="editpage"),
]