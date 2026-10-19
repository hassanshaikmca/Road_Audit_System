from django.urls import path

from . import views
from . import reports

urlpatterns = [
path("", views.home, name="home"),
path("report/<int:audit_id>/", reports.download_audit_report, name="download_audit_report"),
]
