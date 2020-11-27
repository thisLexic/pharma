from django.urls import re_path, path, include

from knox import views as knox_views

from .views import LoginView, StaffView


urlpatterns = [
    # path('api/knox/token', include('knox.urls')),
    path('api/logout/', knox_views.LogoutView.as_view()),
    path('api/login/', LoginView.as_view()),
    path('api/details/', StaffView.as_view()),
]