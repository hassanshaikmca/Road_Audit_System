from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as ReportLabImage,
)

from .models import RoadAudit


def download_audit_report(request, audit_id):
    # Get the selected road audit record
    audit = get_object_or_404(RoadAudit, id=audit_id)

    # Create an in-memory buffer for the PDF
    buffer = BytesIO()

    # Configure PDF document
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    # Load report styles
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            spaceAfter=20,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=18,
            textColor=colors.darkblue,
            spaceBefore=12,
            spaceAfter=8,
        )
    )

    # Content to display inside the PDF
    story = []

    # Report title
    story.append(
        Paragraph(
            "AI Road Audit &amp; Repair Estimation Report",
            styles["ReportTitle"],
        )
    )

    story.append(Spacer(1, 10))

    # Audit information
    story.append(
        Paragraph(
            "Audit Information",
            styles["SectionHeading"],
        )
    )

    audit_date = getattr(audit, "uploaded_at", None)

    if audit_date:
        audit_date = audit_date.strftime("%d-%m-%Y %H:%M")
    else:
        audit_date = "Not available"

    detection_count = getattr(audit, "detection_count", 0) or 0
    estimated_cost = getattr(audit, "estimated_cost", 0) or 0

    audit_data = [
        ["Audit ID", str(audit.id)],
        ["Upload Date", str(audit_date)],
        ["Detected Objects", str(detection_count)],
        ["Estimated Repair Cost", f"Rs. {estimated_cost:,.2f}"],
    ]

    audit_table = Table(
        audit_data,
        colWidths=[2.2 * inch, 4.0 * inch],
    )

    audit_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, -1),
                    colors.black,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    story.append(audit_table)
    story.append(Spacer(1, 20))

    # Uploaded road image
    story.append(
        Paragraph(
            "Uploaded Road Image",
            styles["SectionHeading"],
        )
    )

    if audit.road_image:
        try:
            image_path = Path(audit.road_image.path)

            if image_path.exists():
                road_image = ReportLabImage(
                    str(image_path),
                    width=4.5 * inch,
                    height=2.8 * inch,
                    kind="proportional",
                )

                story.append(road_image)
                story.append(Spacer(1, 15))
            else:
                story.append(
                    Paragraph(
                        "Uploaded image file was not found.",
                        styles["Normal"],
                    )
                )

        except (ValueError, OSError):
            story.append(
                Paragraph(
                    "Uploaded image could not be loaded.",
                    styles["Normal"],
                )
            )

    else:
        story.append(
            Paragraph(
                "No road image is available for this audit.",
                styles["Normal"],
            )
        )

    # AI detection results
    story.append(
        Paragraph(
            "AI Detection Results",
            styles["SectionHeading"],
        )
    )

    # Expected format: audit.detections is a list of dictionaries.
    detections = getattr(audit, "detections", None) or []

    detection_rows = [
        [
            "Class",
            "Confidence",
            "Bounding Box",
        ]
    ]

    for detection in detections:
        if not isinstance(detection, dict):
            continue

        class_name = (
            detection.get("class_name")
            or detection.get("class")
            or detection.get("label")
            or "Unknown"
        )

        confidence = detection.get("confidence", 0)

        try:
            confidence = float(confidence)

            if 0 <= confidence <= 1:
                confidence_text = f"{confidence * 100:.2f}%"
            else:
                confidence_text = f"{confidence:.2f}%"

        except (ValueError, TypeError):
            confidence_text = str(confidence)

        bounding_box = (
            detection.get("bbox")
            or detection.get("box")
            or detection.get("bounding_box")
            or "Not available"
        )

        detection_rows.append(
            [
                str(class_name),
                confidence_text,
                str(bounding_box),
            ]
        )

    if len(detection_rows) == 1:
        detection_rows.append(
            [
                "No detections",
                "-",
                "-",
            ]
        )

    detection_table = Table(
        detection_rows,
        colWidths=[
            2.0 * inch,
            1.4 * inch,
            2.8 * inch,
        ],
        repeatRows=1,
    )

    detection_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.darkblue,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    story.append(detection_table)
    story.append(Spacer(1, 20))

    # Report disclaimer
    story.append(
        Paragraph(
            "Note: Repair cost is an estimate based on the "
            "configured cost per detected object. It should be "
            "verified through an actual road inspection.",
            styles["Italic"],
        )
    )

    # Generate the PDF
    document.build(story)

    # Read the generated PDF
    pdf_data = buffer.getvalue()
    buffer.close()

    # Return PDF as a downloadable response
    response = HttpResponse(
        pdf_data,
        content_type="application/pdf",
    )

    response["Content-Disposition"] = (
        f'attachment; filename="road_audit_report_{audit.id}.pdf"'
    )

    return response