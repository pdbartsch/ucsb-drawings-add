document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const drawingList = document.getElementById('drawing_list').files[0];
    const fileList = document.getElementById('file_list').files[0];
    const firstDrawing = document.getElementById('first_drawing').value;

    if (!drawingList || !fileList) {
        showError('Please select both files');
        return;
    }

    // Show loading state
    const submitBtn = document.getElementById('submitBtn');
    const submitText = document.getElementById('submitText');
    const spinner = document.getElementById('spinner');

    submitBtn.disabled = true;
    submitText.textContent = 'Processing...';
    spinner.classList.remove('d-none');

    try {
        const formData = new FormData();
        formData.append('drawing_list', drawingList);
        formData.append('file_list', fileList);
        formData.append('first_drawing', firstDrawing);

        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.error || 'Unknown error occurred');
            return;
        }

        if (data.success) {
            displayResults(data);
        } else {
            showError(data.error || 'Processing failed');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        submitBtn.disabled = false;
        submitText.textContent = 'Process Files';
        spinner.classList.add('d-none');
    }
});

function showError(message) {
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorAlert.classList.remove('d-none');
    document.getElementById('resultsSection').classList.add('d-none');
}

function resetForm() {
    document.getElementById('errorAlert').classList.add('d-none');
    document.getElementById('resultsSection').classList.add('d-none');
}

function displayResults(data) {
    // Hide error
    document.getElementById('errorAlert').classList.add('d-none');

    // Update counts
    document.getElementById('filesCount').textContent = data.file_list_count;
    document.getElementById('sheetsCount').textContent = data.index_entries_count;

    // Populate table
    const tbody = document.getElementById('resultsTable');
    tbody.innerHTML = '';

    data.mappings.forEach((mapping, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td title="${mapping.old_file_name}">
                ${escapeHtml(mapping.old_file_name)}
            </td>
            <td title="${mapping.file_name}">
                <span class="badge bg-success" style="font-size: 0.75rem; word-break: break-all;">
                    ${escapeHtml(mapping.file_name)}
                </span>
            </td>
            <td>${escapeHtml(mapping.sheet_number || '—')}</td>
            <td>${escapeHtml(mapping.sheet_title || '—')}</td>
        `;
        tbody.appendChild(row);
    });

    // Show results section
    document.getElementById('resultsSection').classList.remove('d-none');

    // Scroll to results
    setTimeout(() => {
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
    }, 100);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
