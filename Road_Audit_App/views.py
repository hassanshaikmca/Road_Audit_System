import logging
from pathlib import Path

import cv2
from PIL import Image, UnidentifiedImageError

from django.conf import settings
from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import render, redirect

from .models import RoadAudit


logger = logging.getLogger(__name__)


# ==========================================
# 1. AI MODEL CONFIGURATION
# ==========================================

def get_yolo_model():
    """
    Load the YOLO model only when image detection is required.
    This prevents the model from loading during Django startup.
    """

    from ultralytics import YOLO

    model_path = settings.BASE_DIR / "best.pt"

    if not model_path.is_file():
        raise FileNotFoundError(
            f"AI model file not found: {model_path}"
        )

    return YOLO(str(model_path))


# ==========================================
# 2. DEMO REPAIR COST CONFIGURATION
# ==========================================

SMALL_POTHOLE_COST = 500
MEDIUM_POTHOLE_COST = 1500
LARGE_POTHOLE_COST = 3000

SMALL_AREA_PERCENT = 1.0
MEDIUM_AREA_PERCENT = 5.0


# ==========================================
# 3. CALCULATE POTHOLE REPAIR COST
# ==========================================

def calculate_pothole_cost(
    x1,
    y1,
    x2,
    y2,
    image_width,
    image_height,
):
    """
    Calculate an illustrative repair cost based on
    the bounding-box area as a percentage of image area.

    These costs are demonstration estimates only.
    """

    box_width = max(0, x2 - x1)
    box_height = max(0, y2 - y1)

    image_area = image_width * image_height

    if image_area <= 0:
        return SMALL_POTHOLE_COST

    box_area_percent = (
        (box_width * box_height) / image_area
    ) * 100

    if box_area_percent < SMALL_AREA_PERCENT:
        return SMALL_POTHOLE_COST

    if box_area_percent < MEDIUM_AREA_PERCENT:
        return MEDIUM_POTHOLE_COST

    return LARGE_POTHOLE_COST


# ==========================================
# 4. DASHBOARD STATISTICS
# ==========================================

def get_dashboard_statistics():
    """
    Return summary statistics for the dashboard.
    """

    total_scans = RoadAudit.objects.count()

    total_detected_objects = (
        RoadAudit.objects.aggregate(
            total=Sum("detection_count")
        )["total"] or 0
    )

    total_repair_cost = (
        RoadAudit.objects.aggregate(
            total=Sum("estimated_cost")
        )["total"] or 0
    )

    recent_audits = RoadAudit.objects.order_by(
        "-uploaded_at"
    )[:5]

    return {
        "total_scans": total_scans,
        "total_detected_objects": total_detected_objects,
        "total_repair_cost": total_repair_cost,
        "recent_audits": recent_audits,
    }


# ==========================================
# 5. HOME PAGE AND IMAGE UPLOAD
# ==========================================

def home(request):
    """
    Display dashboard and process uploaded road images.
    """

    # Display dashboard on GET request
    if request.method == "GET":
        context = get_dashboard_statistics()

        return render(
            request,
            "audits/dashboard.html",
            context,
        )

    # Accept POST requests only for image upload
    if request.method != "POST":
        return redirect("home")

    # Get uploaded road image
    image = request.FILES.get("road_image")

    if not image:
        messages.error(
            request,
            "Please select a road image.",
        )
        return redirect("home")

    # Validate maximum upload size: 5 MB
    if image.size > 5 * 1024 * 1024:
        messages.error(
            request,
            "Image size must be 5 MB or less.",
        )
        return redirect("home")

    # Validate image content
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
            "Invalid image. Please upload a valid image.",
        )
        return redirect("home")

    # Create an audit record and save uploaded image
    audit = RoadAudit.objects.create(
        road_image=image,
    )

    try:
        # Get uploaded image path
        image_path = Path(audit.road_image.path)

        # Load YOLO model only when detection is required
        model = get_yolo_model()

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

        # Get original image dimensions
        image_height, image_width = results[0].orig_shape

        # Prepare detection information
        detections = []

        # Process detections
        for result in results:
            for box in result.boxes:

                # Get detected class
                class_id = int(box.cls[0])
                class_name = model.names[class_id]

                # Get confidence score
                confidence = float(box.conf[0])

                # Get bounding-box coordinates
                coordinates = box.xyxy[0].tolist()

                x1, y1, x2, y2 = [
                    round(float(value), 2)
                    for value in coordinates
                ]

                # Calculate bounding-box dimensions
                box_width = round(
                    max(0, x2 - x1),
                    2,
                )

                box_height = round(
                    max(0, y2 - y1),
                    2,
                )

                # Calculate bounding-box area
                box_area = round(
                    box_width * box_height,
                    2,
                )

                # Estimate repair cost
                pothole_cost = calculate_pothole_cost(
                    x1,
                    y1,
                    x2,
                    y2,
                    image_width,
                    image_height,
                )

                # Store detection details
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
                    "box_width": box_width,
                    "box_height": box_height,
                    "box_area": box_area,
                    "estimated_cost": pothole_cost,
                })

        # Generate annotated image with bounding boxes
        annotated_image = results[0].plot()

        # Create detection-results folder
        output_folder = (
            Path(settings.MEDIA_ROOT)
            / "detection_results"
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Define output image filename
        output_filename = f"audit_{audit.id}_result.jpg"

        output_path = output_folder / output_filename

        # Save annotated image
        image_saved = cv2.imwrite(
            str(output_path),
            annotated_image,
        )

        if not image_saved:
            raise RuntimeError(
                "Unable to save the detection result image."
            )

        # Calculate number of detected objects
        detection_count = len(detections)

        # Calculate total estimated repair cost
        estimated_cost = sum(
            item["estimated_cost"]
            for item in detections
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

    except Exception:
        # Record the complete exception in application logs
        logger.exception(
            "AI detection failed for audit ID %s",
            audit.id,
        )

        messages.warning(
            request,
            "Image uploaded, but AI detection failed. "
            "Check the application logs for details.",
        )

        # Keep the dashboard available if detection fails
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
