document.getElementById('urlForm').addEventListener('submit', function(event) {
    event.preventDefault();

    var inputUrl = document.getElementById('url').value.trim();
    
    fetch('/shorten', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: 'url=' + encodeURIComponent(inputUrl)
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('shortenedUrl').innerHTML = `
            <label for="shortUrl">Shortened URL:</label>
            <input type="text" id="shortUrl" name="shortUrl" value="${data.short_url}" readonly>
            <button id="copyButton" onclick="copyUrl()">Copy URL</button>
        `;
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

function copyUrl() {
    var shortUrlField = document.getElementById('shortUrl');
    shortUrlField.select();
    document.execCommand('copy');
}