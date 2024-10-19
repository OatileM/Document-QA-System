function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    fetch('http://localhost:5000/upload', {
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
            alert(data.message || 'File uploaded successfully');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error uploading file: ' + error.message);
        });
}

function askQuestion() {
    const question = document.getElementById('questionInput').value;
    if (!question) {
        alert('Please enter a question');
        return;
    }

    fetch('http://localhost:5000/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: question }),
        credentials: 'include'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            document.getElementById('response').innerText = data.answer;
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('response').innerText = 'Error: ' + error.message;
        });
}

// Add event listeners when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('fileInput').addEventListener('change', function() {
        const fileName = this.files[0]?.name;
        if (fileName) {
            document.getElementById('fileLabel').textContent = fileName;
        }
    });

    document.getElementById('uploadButton').addEventListener('click', uploadFile);
    document.getElementById('askButton').addEventListener('click', askQuestion);
});
