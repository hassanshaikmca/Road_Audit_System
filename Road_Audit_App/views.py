from pathlib import Path

import cv2
from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO

from django.conf import settings
from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import render, redirect

from .models import RoadAudit


# --------------------------------------------------
# AI MODEL CONFIGURATION
# --------------------------------------------------

MODEL_PATH = settings.BASE_DIR / "best.pt"

model = YOLO(str(MODEL_PATH))

COST_PER_DETECTED_OBJECT = 1000


# --------------------------------------------------
# DASHBOARD STATISTICS
# --------------------------------------------------

def get_dashboard_statistics():

    # Total road audits
    total_scans = RoadAudit.objects.count()

    # Total detected objects across all audits
    total_detected_objects = (
        RoadAudit.objects.aggregate(
            total=Sum("detection_count")
        )["total"] or 0
    )

    # Total estimated repair cost
    total_repair_cost = (
        RoadAudit.objects.aggregate(
            total=Sum("estimated_cost")
        )["total"] or 0
    )

    # Latest five road audits
    recent_audits = RoadAudit.objects.order_by(
        "-uploaded_at"
    )[:5]

    return {
        "total_scans": total_scans,
        "total_detected_objects": total_detected_objects,
        "total_repair_cost": total_repair_cost,
        "recent_audits": recent_audits,
    }


# --------------------------------------------------
# HOME / IMAGE UPLOAD / AI DETECTION
# --------------------------------------------------

def home(request):

    # Display dashboard
    if request.method == "GET":

        context = get_dashboard_statistics()

        return render(
            request,
            "audits/dashboard.html",
            context,
        )

    # Get uploaded image
    image = request.FILES.get("road_image")

    if not image:
        messages.error(
            request,
            "Please select a road image.",
        )

        return redirect("home")

    # Validate image size: maximum 5 MB
    if image.size > 5 * 1024 * 1024:
        messages.error(
            request,
            "Image size must be 5 MB or less.",
        )

        return redirect("home")

    # Validate image format/content
    try:
        with Image.open(image) as uploaded_image:
            uploaded_image.verify()

        image.seek(0)

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):
        messages.error(
            request,
            "Invalid image. Please select a valid image.",
        )

        return redirect("home")

    # Save uploaded image in the database
    audit = RoadAudit.objects.create(
        road_image=image,
    )

    try:

        # Get the uploaded image path
        image_path = Path(audit.road_image.path)

        # Run YOLO object detection
        results = model.predict(
            source=str(image_path),
            conf=0.25,
            save=False,
        )

        if not results:
            raise RuntimeError(
                "The AI model returned no results."
            )

        # Store detection details
        detections = []

        for result in results:

            for box in result.boxes:

                class_id = int(box.cls[0])

                class_name = model.names[class_id]

                confidence = float(box.conf[0])

                coordinates = box.xyxy[0].tolist()

                x1, y1, x2, y2 = [
                    round(float(value), 2)
                    for value in coordinates
                ]

                detections.append({
                    "class_name": class_name,
                    "confidence": round(
                        confidence * 100,
                        2,
                    ),
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                })

        # Generate image with detection boxes
        annotated_image = results[0].plot()

        # Create output directory
        output_folder = (
            Path(settings.MEDIA_ROOT)
            / "detection_results"
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Save annotated image
        output_filename = (
            f"audit_{audit.id}_result.jpg"
        )

        output_path = output_folder / output_filename

        if not cv2.imwrite(
            str(output_path),
            annotated_image,
        ):
            raise RuntimeError(
                "Unable to save detection result image."
            )

        # Calculate detection count and estimated cost
        detection_count = len(detections)

        estimated_cost = (
            detection_count
            * COST_PER_DETECTED_OBJECT
        )

        # Update audit record
        audit.detection_count = detection_count

        audit.estimated_cost = estimated_cost

        audit.detections = detections

        audit.save(
            update_fields=[
                "detection_count",
                "estimated_cost",
                "detections",
            ]
        )

        # Refresh dashboard statistics
        context = get_dashboard_statistics()

        context.update({
            "audit": audit,
            "detections": detections,
            "detection_count": detection_count,
            "annotated_image_url": (
                f"{settings.MEDIA_URL}"
                f"detection_results/{output_filename}"
            ),
            "estimated_cost": estimated_cost,
        })

        messages.success(
            request,
            "Image uploaded and AI detection completed.",
        )

        return render(
            request,
            "audits/dashboard.html",
            context,
        )

    except Exception as error:

        # Print the actual error in the terminal
        print(
            "AI Detection Error:",
            error,
        )

        messages.warning(
            request,
            "Image uploaded, but AI detection failed. "
            "Check the terminal for details.",
        )

        # Display dashboard even if detection fails
        context = get_dashboard_statistics()

        context.update({
            "audit": audit,
            "detections": [],
            "detection_count": 0,
            "annotated_image_url": None,
            "estimated_cost": None,
        })

        return render(
            request,
            "audits/dashboard.html",
            context,
        )
