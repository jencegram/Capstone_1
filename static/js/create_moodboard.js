// Array to store selected image URLs
let selectedImages = [];

function searchImages() {
    // Function to handle image search
    const query = document.getElementById('image-search').value;

    // Make an AJAX request to your /search_photos route
    fetch(`/search_photos?query=${query}`)
        .then(response => response.json())
        .then(data => {
            // Process search results and update the selected images
            const selectedImagesContainer = document.getElementById('selected-images-preview');
            selectedImagesContainer.innerHTML = '';


            if (data && data.photos && data.photos.length > 0) {
                data.photos.forEach(photo => {
                    const imageContainer = document.createElement('div');
                    imageContainer.className = 'selected-image-container';
                    const image = document.createElement('img');
                    image.src = photo.urls.regular;
                    image.alt = photo.alt_description;
                    image.width = 250;
                    image.height = 250;
                    imageContainer.appendChild(image);

                    // Attach a click event to each image for selection
                    image.addEventListener('click', () => toggleSelectImage(image, photo.urls.regular));

                    selectedImagesContainer.appendChild(imageContainer);
                });
            } else {
                selectedImagesContainer.innerHTML = '<p>No Images Found</p>';
            }
        })
        .catch(error => {
            console.error('Error fetching photos:', error);
        });
}

// Function to toggle image selection
function toggleSelectImage(image, imageUrl) {
    const index = selectedImages.indexOf(imageUrl);
    if (index === -1) {
        // Image is not selected, so add it to the selectedImages array
        selectedImages.push(imageUrl);
        image.classList.add('selected-image');
    } else {
        // Image is already selected, so remove it from the selectedImages array
        selectedImages.splice(index, 1);
        image.classList.remove('selected-image');
    }
}

// Add selected images to the form
function addSelectedImagesToForm() {
    const selectedImagesPreview = document.getElementById('selected-images-preview');

    selectedImagesPreview.innerHTML = '';

    // Add selected images as hidden input fields
    selectedImages.forEach(imageUrl => {
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'selected_images[]';  // Array for multiple images
        hiddenInput.value = imageUrl;
        selectedImagesPreview.appendChild(hiddenInput);
    });
}

// Function to handle form submission
function handleFormSubmit() {
    // Add the selected images to the form
    addSelectedImagesToForm();

    const form = document.getElementById('create-moodboard-form');
    form.submit();
}
