// 1. Get HTML elements
const form = document.getElementById("upload-form");
const fileInput = document.getElementById("road-image");
const previewContainer = document.getElementById("preview-container");
const imagePreview = document.getElementById("image-preview");
const statusMessage = document.getElementById("status-message");


// 2. Maximum image size: 5 MB
const maxFileSize = 5 * 1024 * 1024;


// 3. Show image preview when user selects an image
fileInput.addEventListener("change", function () {

    // Get the selected image
    const file = fileInput.files[0];

    // Clear the previous preview
    imagePreview.removeAttribute("src");
    previewContainer.hidden = true;
    statusMessage.textContent = "";

    // Check whether an image was selected
    if (!file) {
        return;
    }

    // Check image file type
    if (!file.type.startsWith("image/")) {

        statusMessage.textContent =
            "Please select a valid image.";

        fileInput.value = "";
        return;
    }

    // Check image file size
    if (file.size > maxFileSize) {

        statusMessage.textContent =
            "Image must be 5 MB or less.";

        fileInput.value = "";
        return;
    }

    // Display the selected image
    const imageUrl = URL.createObjectURL(file);

    imagePreview.src = imageUrl;
    previewContainer.hidden = false;

    // Display success message
    statusMessage.textContent =
        "Image selected successfully.";

});


// 4. Validate the image before uploading
form.addEventListener("submit", function (event) {

    // Get the selected image
    const file = fileInput.files[0];

    // Check if an image was selected
    if (!file) {

        event.preventDefault();

        statusMessage.textContent =
            "Please select a road image first.";

        return;
    }

    // Check image type again
    if (!file.type.startsWith("image/")) {

        event.preventDefault();

        statusMessage.textContent =
            "Please select a valid image.";

        return;
    }

    // Check image size again
    if (file.size > maxFileSize) {

        event.preventDefault();

        statusMessage.textContent =
            "Image must be 5 MB or less.";

        return;
    }

    // Show upload message
    statusMessage.textContent =
        "Uploading image. Please wait...";

    // The form will now submit to the Django backend.
});


// 5. Prevent the browser from displaying a broken preview
imagePreview.addEventListener("error", function () {

    previewContainer.hidden = true;

    statusMessage.textContent =
        "Unable to preview this image. Please select another image.";

});