
// Allows users to search and select new images from Unsplash

// Add an event listener to the search button to trigger a search when clicked.
document.getElementById("search-button").addEventListener("click", function () {
    let query = document.getElementById("search-query").value;

    // Fetch photos from the server using the search term.
    fetch(`/search_photos?query=${query}`)
        .then(response => response.json())
        .then(data => {
            // Get the search results container to display fetched photos.
            let searchResults = document.getElementById("search-results");
            searchResults.innerHTML = "";

            // Loop through each photo in the returned data.
            data.photos.forEach(photo => {
                // Create a new image element for the photo.
                let img = document.createElement("img");
                img.src = photo.urls.small;
                img.dataset.url = photo.urls.full;
                img.width = 250;
                img.height = 250;

                // Add an event listener to the image for selecting/deselecting it.
                img.addEventListener("click", function () {
                    if (!this.classList.contains("selected-image")) {
                        this.classList.add("selected-image");
                        let hiddenInput = document.createElement("input");
                        hiddenInput.type = "hidden";
                        hiddenInput.name = "selected_images[]";
                        hiddenInput.value = this.dataset.url;
                        document.querySelector("form").appendChild(hiddenInput);
                    } else {
                        this.classList.remove("selected-image");
                        let hiddenInputs = document.querySelectorAll(`input[value="${this.dataset.url}"]`);
                        hiddenInputs.forEach(input => input.remove());
                    }
                });
                // Add the image to the search results container.
                searchResults.appendChild(img);
            });
        });
});
