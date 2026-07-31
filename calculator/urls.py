from django.urls import path
from .views import stat_check_view

app_name = "calculator"

urlpatterns = [
    path("", stat_check_view, name="stat-check"),
]
