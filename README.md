# AI Road Audit & Repair Estimation System

An AI-powered road inspection web application built using Python, Django, and YOLO. The application allows users to upload road images, detect road defects, calculate an estimated repair cost, and download PDF audit reports.

## Features

* Upload road images
* Validate uploaded images
* Detect road defects using a YOLO model
* Display AI detection results
* Generate annotated images with detection boxes
* Count detected objects
* Estimate repair costs
* Display dashboard statistics
* Store road audit records
* View recent road audits
* Download PDF audit reports

## Technologies Used

* Python
* Django
* Ultralytics YOLO
* OpenCV
* Pillow
* ReportLab
* SQLite
* HTML
* CSS
* JavaScript

## Project Structure

```text
Road_Audit_System/
│
├── .Road/
├── Road_Audit_Project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── Road_Audit_App/
│   ├── migrations/
│   ├── templates/
│   │   └── audits/
│   │       └── dashboard.html
│   ├── static/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── reports.py
│   ├── admin.py
│   └── apps.py
│
├── media/
├── best.pt
├── manage.py
├── requirements.txt
├── README.md
└── .gitignore
```

The exact folder structure may vary depending on your implementation. The `.Road` directory contains the Python virtual environment.

## Prerequisites

Install the following before running the project:

* Python
* pip
* A compatible YOLO model file named `best.pt`

## Installation

### 1. Open the project directory

```powershell
cd "C:\Users\styli\OneDrive\Desktop\Road_Audit_System"
```

### 2. Activate the virtual environment

```powershell
.\.Road\Scripts\Activate.ps1
```

If PowerShell does not allow activation, open Command Prompt and run:

```bat
.\.Road\Scripts\activate.bat
```

### 3. Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### 4. Install the required libraries

```powershell
python -m pip install Django Pillow ultralytics opencv-python reportlab
```

### 5. Generate requirements.txt

```powershell
python -m pip freeze > requirements.txt
```

### 6. Install dependencies from requirements.txt

```powershell
python -m pip install -r requirements.txt
```

## AI Model Setup

Place the compatible trained YOLO model file in the project root directory:

```text
Road_Audit_System/best.pt
```

The application loads the model from this location.

If the model file is missing or incompatible, AI detection will not work correctly.

## Database Setup

### 1. Check the Django project

```powershell
python manage.py check
```

### 2. Create model migrations

```powershell
python manage.py makemigrations Road_Audit_App
```

### 3. Apply migrations

```powershell
python manage.py migrate
```

Django uses SQLite by default unless another database is configured in `settings.py`.

## Run the Application

Start the development server:

```powershell
python manage.py runserver
```

Open the application:

http://127.0.0.1:8000/

Stop the development server by pressing `CTRL + C`.

## How to Use

1. Start the Django server.
2. Open the dashboard in a browser.
3. Select a road image.
4. Upload the image.
5. Wait for AI detection to complete.
6. Review detected objects and confidence values.
7. Review the estimated repair cost.
8. Download the PDF audit report.
9. Review recent audit records if the dashboard history section is configured.

## Repair Cost Calculation

The current example implementation uses a fixed cost per detected object:

```python
COST_PER_DETECTED_OBJECT = 1000
```

The estimated cost is calculated using:

```python
estimated_cost = detection_count * COST_PER_DETECTED_OBJECT
```

For example, if three objects are detected, the estimated cost is ₹3,000.

This is a demonstration calculation, not an official repair quotation. Actual costs depend on defect dimensions, defect type, materials, labor, and local rates.

## Media Configuration

In `Road_Audit_Project/settings.py`, configure:

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

Uploaded road images are stored under:

```text
media/road_images/
```

Annotated detection results are stored under:

```text
media/detection_results/
```

Ensure that media URLs are configured for local development. Do not expose uploaded files publicly in production without appropriate access controls.

## Useful Django Commands

Check configuration:

```powershell
python manage.py check
```

Create migrations:

```powershell
python manage.py makemigrations
```

Apply migrations:

```powershell
python manage.py migrate
```

Create an administrator account:

```powershell
python manage.py createsuperuser
```

Run the development server:

```powershell
python manage.py runserver
```

Run on another port:

```powershell
python manage.py runserver 8001
```

## Troubleshooting

### Missing Python package

Activate the virtual environment and install the required packages:

```powershell
python -m pip install Django Pillow ultralytics opencv-python reportlab
```

### Missing YOLO model

Confirm that `best.pt` exists in the project root.

### Database migration error

Run:

```powershell
python manage.py makemigrations
python manage.py migrate
```

### Image upload error

Verify that the upload form uses:

* `method="POST"`
* `enctype="multipart/form-data"`
* An image input named `road_image`
* Django's CSRF token

Also check the media configuration and the terminal error message.

### PDF report error

Verify that `Road_Audit_App/reports.py` exists and that ReportLab is installed.

## Future Improvements

* Improve detection accuracy
* Train a custom YOLO model on a road damage dataset
* Classify different road defects
* Improve cost estimation using defect dimensions and repair rates
* Add email delivery of PDF reports
* Add user authentication
* Add audit filtering and search
* Deploy the application to a production server

## Disclaimer

This project is intended for educational and demonstration purposes. AI detections and repair estimates should be verified by qualified personnel before being used for official road maintenance decisions.

## Project Information

**Project:** AI Road Audit & Repair Estimation System
**Backend:** Django
**AI Detection:** Ultralytics YOLO
**Language:** Python
**Database:** SQLite by default
