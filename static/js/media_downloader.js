document.addEventListener('DOMContentLoaded', function () {
    // YouTube Audio
    const youtubeForm = document.getElementById('youtube-form');
    if (youtubeForm) {
        youtubeForm.addEventListener('submit', function (e) {
            e.preventDefault();
            handleDownloadForm(this, 'audio');
        });
    }

    // Pinterest
    const pinterestForm = document.getElementById('pinterest-form');
    if (pinterestForm) {
        pinterestForm.addEventListener('submit', function (e) {
            e.preventDefault();
            handleDownloadForm(this, 'video');
        });
    }

    // Social (Shorts / Reels / TikTok)
    const socialForm = document.getElementById('social-form');
    if (socialForm) {
        socialForm.addEventListener('submit', function (e) {
            e.preventDefault();
            handleDownloadForm(this, 'social');
        });
    }

    // Main handler
    function handleDownloadForm(form, type) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

        const downloadStatus = document.getElementById('download-status');
        downloadStatus.style.display = 'block';

        const downloadsContainer = document.getElementById('downloads-container');
        const downloadId = 'download-' + Date.now();
        const downloadItem = document.createElement('div');
        downloadItem.id = downloadId;
        downloadItem.className = 'download-item mb-3 p-3 border rounded';
        downloadItem.innerHTML = `
            <div class="download-item-header d-flex justify-content-between mb-2">
                <span class="download-item-title">${formatType(type)}</span>
                <span class="download-item-status">Processing...</span>
            </div>
            <div class="progress mb-2">
                <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 100%"></div>
            </div>
        `;
        downloadsContainer.appendChild(downloadItem);

        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const statusElem = downloadItem.querySelector('.download-item-status');
            const progressBar = downloadItem.querySelector('.progress-bar');

            if (data.success) {
                statusElem.textContent = 'Completed';
                statusElem.className = 'download-item-status text-success';
                progressBar.classList.remove('progress-bar-animated');
                progressBar.style.width = '100%';

                // Download button
                const downloadBtn = document.createElement('a');
                downloadBtn.href = data.download_url;
                downloadBtn.className = 'btn btn-sm btn-success mt-2 me-2';
                downloadBtn.innerHTML = '<i class="fas fa-download me-1"></i>Download Now';
                downloadBtn.setAttribute('download', data.filename);
                downloadItem.appendChild(downloadBtn);

                // Copy URL button
                const copyBtn = document.createElement('button');
                copyBtn.className = 'btn btn-sm btn-outline-secondary mt-2';
                copyBtn.innerHTML = '<i class="fas fa-copy me-1"></i>Copy URL';
                copyBtn.onclick = () => navigator.clipboard.writeText(data.download_url);
                downloadItem.appendChild(copyBtn);

                // Reset form
                form.reset();
            } else {
                statusElem.textContent = 'Failed: ' + (data.error || 'Unknown error');
                statusElem.className = 'download-item-status text-danger';
                progressBar.classList.remove('progress-bar-animated', 'progress-bar-striped');
                progressBar.classList.add('bg-danger');
                progressBar.style.width = '100%';
            }

            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        })
        .catch(error => {
            const statusElem = downloadItem.querySelector('.download-item-status');
            statusElem.textContent = 'Error: ' + error.message;
            statusElem.className = 'download-item-status text-danger';

            const progressBar = downloadItem.querySelector('.progress-bar');
            progressBar.classList.remove('progress-bar-animated', 'progress-bar-striped');
            progressBar.classList.add('bg-danger');
            progressBar.style.width = '100%';

            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        });
    }

    // Helper to format title
    function formatType(type) {
        switch (type) {
            case 'audio': return 'YouTube Audio';
            case 'video': return 'Pinterest Video';
            case 'social': return 'Shorts / Reels / TikTok';
            default: return 'Media Download';
        }
    }
});
