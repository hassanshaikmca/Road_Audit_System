"""
URL configuration for the Road Audit System.
"""

from django.contrib import admin
from django.urls import path, include

# Import Django settings to configure media files.
from django.conf import settings

# Helper for serving uploaded media files during development.
from django.conf.urls.static import static


# ==================================================
# MAIN URL PATTERNS
# ==================================================

urlpatterns = [

    # Django administration page.
    path("admin/", admin.site.urls),

    # Connect the Road Audit application URLs.
    path("", include("Road_Audit_App.urls")),

]


# ==================================================
# MEDIA FILE CONFIGURATION
# ==================================================

# Serve uploaded images during local development.
# Production media files should be served by a suitable
# web server or storage service.

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
