// AIT CTF Frontend JavaScript

// Function to show flash messages temporarily
function showFlashMessage(message, type = 'info') {
    const flashDiv = document.createElement('div');
    flashDiv.className = `flash flash-${type}`;
    flashDiv.textContent = message;

    const container = document.querySelector('main') || document.body;
    container.insertBefore(flashDiv, container.firstChild);

    setTimeout(() => {
        flashDiv.remove();
    }, 5000);
}

// Function to confirm delete actions
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

// Function to validate flag format
function validateFlag(flag) {
    const flagRegex = /^AITCTF\{.*\}$/;
    return flagRegex.test(flag);
}

// Add event listener to flag submission forms
document.addEventListener('DOMContentLoaded', function() {
    const flagForm = document.querySelector('.flag-form');
    if (flagForm) {
        flagForm.addEventListener('submit', function(e) {
            const flagInput = document.getElementById('flag');
            if (flagInput && !validateFlag(flagInput.value)) {
                e.preventDefault();
                showFlashMessage('Flag must be in the format: AITCTF{flag_here}', 'error');
                return false;
            }
        });
    }

    // Add loading indicators for form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.textContent = 'Submitting...';
                submitBtn.disabled = true;
            }
        });
    });
});

// Function to copy text to clipboard (for sharing challenge links)
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showFlashMessage('Link copied to clipboard!', 'success');
    }, function(err) {
        console.error('Could not copy text: ', err);
    });
}

// Add click handlers for challenge cards (if needed for future features)
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('challenge-card')) {
        // Could add expand/collapse functionality here
    }
});
