from django.db import models


class RoadAudit(models.Model):
    road_image = models.ImageField(upload_to="road_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    detection_count = models.PositiveIntegerField(default=0)
    estimated_cost = models.PositiveIntegerField(default=0)
    detections = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Road Audit {self.id}"
