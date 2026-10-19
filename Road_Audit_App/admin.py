from django.contrib import admin
from .models import RoadAudit
# Register your models here.
admin.site.register(RoadAudit)
class RoadAuditAdmin(admin.ModelAdmin):
    list_display = ('id', 'road_image', 'uploaded_at')
    ordering = ('-uploaded_at',)