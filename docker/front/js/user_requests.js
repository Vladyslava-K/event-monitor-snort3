document.getElementById('dataForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const errorDisplay = document.getElementById('errorDisplay');
    errorDisplay.innerHTML = ''; // Clear existing data
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = ''; // Clear existing data

    const periodStart = document.getElementById('periodStart').value;
    const periodEnd = document.getElementById('periodEnd').value;
    const queryParams = `period_start=${periodStart}&period_end=${periodEnd}`;

    loadUserRequests(`http://127.0.0.1:8000/api/v1/requests-log?${queryParams}`);
});


function loadUserRequests(url) {
    fetch(url)
        .then(response => {
            if (response.status === 400) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Bad request');
                });
            }

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            return response.json();
        })
        .then(data => {
            displayData(data);
            updatePagination(data.next, data.previous);
        })
        .catch(error => {
            console.error('Fetch error:', error);
            document.getElementById('errorDisplay').innerHTML = `<div class="alert alert-danger" role="alert">${error.message}</div>`;
        });
}

document.addEventListener('DOMContentLoaded', (event) => {
    const prevPage = document.getElementById('prevPage');
    const nextPage = document.getElementById('nextPage');

    prevPage.addEventListener('click', (e) => {
        e.preventDefault();
        const url = e.target.getAttribute('data-url');
        if (url) {
            loadUserRequests(url);
        }
    });

    nextPage.addEventListener('click', (e) => {
        e.preventDefault();
        const url = e.target.getAttribute('data-url');
        if (url) {
            loadUserRequests(url);
        }
    });
});

function updatePagination(next, prev) {
    const prevPage = document.getElementById('prevPage');
    const nextPage = document.getElementById('nextPage');

    if (prev) {
        prevPage.classList.remove('disabled');
        prevPage.firstChild.setAttribute('data-url', prev);
    } else {
        prevPage.classList.add('disabled');
        prevPage.firstChild.removeAttribute('data-url');
    }

    if (next) {
        nextPage.classList.remove('disabled');
        nextPage.firstChild.setAttribute('data-url', next);
    } else {
        nextPage.classList.add('disabled');
        nextPage.firstChild.removeAttribute('data-url');
    }
}

document.getElementById('userRequestsLink').addEventListener('click', function() {
    loadUserRequests();
});

function displayData(data) {
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = ''; // Clear existing data

    if (data.results && Array.isArray(data.results)) {
        data.results.forEach(item => {
            // Create a string with all request data parameters
            const requestDataContent = Object.entries(item.request_data).map(([key, value]) => {
                return `${key}: ${value.join(', ')}`;
            }).join('<br>');

            const row = `
                <tr>
                    <td>${item.id}</td>
                    <td>${item.timestamp}</td>
                    <td>${item.user_ip}</td>
                    <td>${item.http_method}</td>
                    <td>${item.response_status_code}</td>
                    <td>${item.endpoint}</td>
                    <td>${requestDataContent}</td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });
    } else {
        tableBody.innerHTML = '<tr><td colspan="7">No data found.</td></tr>';
    }
}