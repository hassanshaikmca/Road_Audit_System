"""
Views for the AI Road Audit System.

Main features:
1. Display dashboard statistics.
2. Upload road images.
3. Detect road defects using YOLO.
4. Calculate estimated repair costs.
5. Save detection results.
6. Display the processed images.
"""

import logging
from pathlib import Path

import cv2
from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO

from django.conf import settings
from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import render

from .models import RoadAudit


# ==================================================
# 1. LOGGER CONFIGURATION
# ==================================================

# Record errors to help us identify problems.
logger = logging.getLogger(__name__)


# ==================================================
# 2. AI MODEL CONFIGURATION
# ==================================================

# Location of the trained YOLO model.
MODEL_PATH = settings.BASE_DIR / "best.pt"

# Keep the model unloaded until it is needed.
# This avoids loading the model unnecessarily.
_model = None


def get_yolo_model():
    """
    Load the YOLO model when it is first required.

    The loaded model is reused for later requests.
    """

    global _model

    # Load the model only once.
    if _model is None:

        # Check whether the model file exists.
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"YOLO model not found at: {MODEL_PATH}"
            )

        # Load the trained YOLO model.
        _model = YOLO(str(MODEL_PATH))

    return _model


# ==================================================
# 3. REPAIR COST CONFIGURATION
# ==================================================

# Estimated repair costs in Indian Rupees.
# These are example estimates and should be calibrated
# using actual repair costs for your area.

REPAIR_COSTS = {
    "small": 500,
    "medium": 1500,
    "large": 3000,
}

# Thresholds based on the defect bounding-box area
# relative to the complete road image.
SMALL_AREA_THRESHOLD = 0.01
MEDIUM_AREA_THRESHOLD = 0.05


def calculate_repair_cost(box_area, image_area):
    """
    Estimate the repair cost based on defect size.

    Parameters:
        box_area: Area of the detected bounding box.
        image_area: Total area of the road image.

    Returns:
        Estimated repair cost in rupees.
    """

    # Avoid division by zero.
    if image_area <= 0:
        return 0

    # Calculate the fraction of the image covered by the box.
    area_ratio = box_area / image_area

    # Assign a cost based on the detected area.
    if area_ratio < SMALL_AREA_THRESHOLD:
        return REPAIR_COSTS["small"]

    elif area_ratio < MEDIUM_AREA_THRESHOLD:
        return REPAIR_COSTS["medium"]

    return REPAIR_COSTS["large"]


# ==================================================
# 4. DASHBOARD STATISTICS
# ==================================================

def get_dashboard_statistics():
    """
    Calculate the total scans, detected objects,
    and estimated repair costs.
    """

    # Count all saved road audits.
    total_scans = RoadAudit.objects.count()

    # Add the number of detected objects across audits.
    total_detected_objects = (
        RoadAudit.objects.aggregate(
            total=Sum("detection_count")
        )["total"]
        or 0
    )

    # Add the estimated repair costs across audits.
    total_repair_cost = (
        RoadAudit.objects.aggregate(
            total=Sum("estimated_cost")
        )["total"]
        or 0
    )

    # Return all dashboard statistics.
    return {
        "total_scans": total_scans,
        "total_detected_objects": total_detected_objects,
        "total_repair_cost": total_repair_cost,
    }


# ==================================================
# 5. PREPARE THE DASHBOARD CONTEXT
# ==================================================

def get_dashboard_context():
    """
    Prepare the information required by dashboard.html.
    """

    # Start with an empty dictionary.
    context = {}

    # Add the dashboard statistics.
    context.update(get_dashboard_statistics())

    return context


# ==================================================
# 6. MAIN DASHBOARD VIEW
# ==================================================

def home(request):
    """
    Display the dashboard and process uploaded road images.
    """

    # --------------------------------------------------
    # STEP 1: HANDLE A NORMAL PAGE REQUEST
    # --------------------------------------------------

    # If the user has not submitted an image,
    # display the dashboard.
    if request.method != "POST":

        context = get_dashboard_context()

        return render(
            request,
            "audits/dashboard.html",
            context,
        )

    # --------------------------------------------------
    # STEP 2: GET THE UPLOADED IMAGE
    # --------------------------------------------------

    # Read the image selected in the upload form.
    uploaded_file = request.FILES.get("road_image")

    # Check whether the user selected a file.
    if not uploaded_file:

        messages.error(
            request,
            "Please select a road image before uploading.",
        )

        return render(
            request,
            "audits/dashboard.html",
            get_dashboard_context(),
        )

    # --------------------------------------------------
    # STEP 3: CHECK THE FILE SIZE
    # --------------------------------------------------

    # Maximum allowed image size: 5 MB.
    MAX_FILE_SIZE = 5 * 1024 * 1024

    # Reject files larger than the allowed size.
    if uploaded_file.size > MAX_FILE_SIZE:

        messages.error(
            request,
            "Image size must be 5 MB or less.",
        )

        return render(
            request,
            "audits/dashboard.html",
            get_dashboard_context(),
        )

    # Reject empty files.
    if uploaded_file.size == 0:

        messages.error(
            request,
            "The selected file is empty.",
        )

        return render(
            request,
            "audits/dashboard.html",
            get_dashboard_context(),
        )

    # --------------------------------------------------
    # STEP 4: VALIDATE THE IMAGE CONTENT
    # --------------------------------------------------

    try:

        # Open the uploaded file using Pillow.
        with Image.open(uploaded_file) as image:

            # Verify that the image file is valid.
            image.verify()

        # Reset the file pointer so Django can save it.
        uploaded_file.seek(0)

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):

        messages.error(
            request,
            "Invalid image file. Please upload a valid image.",
        )

        return render(
            request,
            "audits/dashboard.html",
            get_dashboard_context(),
        )

    # --------------------------------------------------
    # STEP 5: CREATE THE ROAD AUDIT RECORD
    # --------------------------------------------------

    audit = None

    try:

        # Save the original image and create a database record.
        audit = RoadAudit.objects.create(
            road_image=uploaded_file,
            detection_count=0,
            estimated_cost=0,
            detections=[],
        )

        # Get the full path of the saved image.
        image_path = audit.road_image.path

        # --------------------------------------------------
        # STEP 6: READ THE IMAGE USING OPENCV
        # --------------------------------------------------

        # Read the saved image.
        road_image = cv2.imread(image_path)

        # Check whether OpenCV successfully read the image.
        if road_image is None:

            raise ValueError(
                "OpenCV could not read the uploaded image."
            )

        # Get the image height and width.
        image_height, image_width = road_image.shape[:2]

        # Calculate the complete image area.
        image_area = image_width * image_height

        # --------------------------------------------------
        # STEP 7: LOAD THE YOLO MODEL
        # --------------------------------------------------

        # Load the trained model.
        model = get_yolo_model()

        # --------------------------------------------------
        # STEP 8: RUN ROAD DEFECT DETECTION
        # --------------------------------------------------

        # Run the model on the uploaded image.
        results = model.predict(
            source=image_path,
            conf=0.25,
            save=False,
            verbose=False,
        )

        # Create an empty list to store detections.
        detections = []

        # Store the total estimated repair cost.
        total_estimated_cost = 0

        # --------------------------------------------------
        # STEP 9: PROCESS DETECTION RESULTS
        # --------------------------------------------------

        # Process each prediction result.
        for result in results:

            # Get the detected bounding boxes.
            boxes = result.boxes

            # Continue if no boxes were detected.
            if boxes is None:
                continue

            # Process each detected object.
            for box in boxes:

                # Get the coordinates of the bounding box.
                coordinates = box.xyxy[0].tolist()

                # Convert coordinates to integers.
                x1, y1, x2, y2 = [
                    int(value)
                    for value in coordinates
                ]

                # Calculate the bounding-box width.
                box_width = max(0, x2 - x1)

                # Calculate the bounding-box height.
                box_height = max(0, y2 - y1)

                # Calculate the bounding-box area.
                box_area = box_width * box_height

                # Get the detected class ID.
                class_id = int(box.cls[0].item())

                # Get the class name from the trained model.
                class_name = model.names.get(
                    class_id,
                    str(class_id),
                )

                # Convert confidence to a percentage.
                confidence = float(box.conf[0].item()) * 100

                # Estimate the repair cost for this detection.
                repair_cost = calculate_repair_cost(
                    box_area,
                    image_area,
                )

                # Add this object's cost to the total.
                total_estimated_cost += repair_cost

                # Save the detection details.
                detections.append(
                    {
                        "class_name": str(class_name),
                        "confidence": round(confidence, 2),
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "box_width": box_width,
                        "box_height": box_height,
                        "box_area": box_area,
                        "estimated_cost": repair_cost,
                    }
                )

        # --------------------------------------------------
        # STEP 10: SAVE THE ANNOTATED IMAGE
        # --------------------------------------------------

        # Create the directory for detection results.
        result_directory = (
            Path(settings.MEDIA_ROOT)
            / "detection_results"
        )

        result_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Create a unique filename for this audit.
        result_filename = f"audit_{audit.id}_result.jpg"

        # Get the complete output path.
        result_path = result_directory / result_filename

        # Draw bounding boxes and labels on the image.
        annotated_image = results[0].plot()

        # Save the annotated image.
        image_saved = cv2.imwrite(
            str(result_path),
            annotated_image,
        )

        # Check whether the image was saved successfully.
        if not image_saved:

            raise OSError(
                "Failed to save the annotated detection image."
            )

        # --------------------------------------------------
        # STEP 11: UPDATE THE DATABASE RECORD
        # --------------------------------------------------

        # Save the detection count.
        audit.detection_count = len(detections)

        # Save the total estimated repair cost.
        audit.estimated_cost = total_estimated_cost

        # Save all detection details.
        audit.detections = detections

        # Update the database.
        audit.save(
            update_fields=[
                "detection_count",
                "estimated_cost",
                "detections",
            ]
        )

        # --------------------------------------------------
        # STEP 12: PREPARE THE SUCCESSFUL RESPONSE
        # --------------------------------------------------

        # Get the dashboard statistics.
        context = get_dashboard_context()

        # Add the latest audit information.
        context.update(
            {
                "audit": audit,
                "detections": detections,
                "detection_count": len(detections),
                "annotated_image_url": (
                    f"{settings.MEDIA_URL}"
                    f"detection_results/{result_filename}"
                ),
                "estimated_cost": total_estimated_cost,
            }
        )

        # Display a success message.
        messages.success(
            request,
            "Road image processed successfully!",
        )

        # Display the dashboard with the results.
        return render(
            request,
            "audits/dashboard.html",
            context,
        )

    # --------------------------------------------------
    # STEP 13: HANDLE PROCESSING ERRORS
    # --------------------------------------------------

    except Exception:

        # Record the complete error details in the server log.
        logger.exception(
            "An error occurred while processing the road image."
        )

        # Inform the user without displaying internal details.
        messages.error(
            request,
            "Unable to process the image. "
            "Please check the server terminal for details.",
        )

        # Prepare the dashboard context.
        context = get_dashboard_context()

        # Display the audit information if available.
        if audit is not None:

            context.update(
                {
                    "audit": audit,
                    "detections": [],
                    "detection_count": 0,
                    "annotated_image_url": None,
                    "estimated_cost": None,
                }
            )

        # Return the dashboard with an error message.
        return render(
            request,
            "audits/dashboard.html",
            context,
        )
