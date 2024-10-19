function uploadFile(file) {
    if (!file) {
        alert('Please select a file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    // Show loading state
    const uploadStatus = document.getElementById('uploadStatus');
    uploadStatus.textContent = 'Uploading...';

    fetch('http://127.0.0.1:5000/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Upload successful:', data);
        uploadStatus.textContent = data.message || 'File uploaded successfully';
    })
    .catch(error => {
        console.error('Error:', error);
        uploadStatus.textContent = 'Error uploading file: ' + error.message;
    });
}

function askQuestion() {
    const question = document.getElementById('questionInput').value;
    if (!question) {
        alert('Please enter a question');
        return;
    }

    const askButton = document.getElementById('askButton');
    const responseElement = document.getElementById('response');

    askButton.disabled = true;
    askButton.textContent = 'Processing...';
    responseElement.textContent = 'Thinking...';

    fetch('http://127.0.0.1:5000/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: question }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(`Server error: ${errorData.error || response.statusText}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        responseElement.textContent = data.answer;
    })
    .catch(error => {
        console.error('Error details:', error);
        responseElement.textContent = 'Error: ' + error.message;
    })
    .finally(() => {
        askButton.disabled = false;
        askButton.textContent = 'Ask';
    });
}

// Add event listeners when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    
    fileInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            uploadFile(file);
        }
    });

    document.getElementById('askButton').addEventListener('click', askQuestion);
});
