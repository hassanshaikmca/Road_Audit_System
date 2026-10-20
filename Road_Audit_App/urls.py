"""
URL configuration for the Road Audit application.
"""

from django.urls import path

# Import the dashboard views.
from . import views

# Import the PDF report functionality.
from . import reports


# Define application URL patterns.
urlpatterns = [

    # Display the main dashboard.
    # URL: http://127.0.0.1:8000/
    path(
        "",
        views.home,
        name="home",
    ),

    # Download the PDF report for a particular audit.
    # Example: http://127.0.0.1:8000/report/1/
    path(
        "report/<int:audit_id>/",
        reports.download_audit_report,
        name="download_audit_report",
    ),

]
