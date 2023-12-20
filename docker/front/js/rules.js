let currentPage = 1;

document.addEventListener('DOMContentLoaded', function() {
    getSnortRules();
});


function getSnortRules(newSearch = true) {
    if (newSearch) {
        currentPage = 1;
    }

    const gid = document.getElementById('gid').value;
    const sid = document.getElementById('sid').value;
    const action = document.getElementById('action').value;

    const requestData = {
        page: currentPage,
    };

    if (gid.trim() !== '') {
        requestData.gid = gid.trim();
    }

    if (sid.trim() !== '') {
        requestData.sid = sid.trim();
    }

    if (action.trim() !== '') {
        requestData.action = action.trim();
    }

    const queryString = new URLSearchParams(requestData).toString();
    const apiUrl = `http://127.0.0.1:8000/api/v1/rules?${queryString}`;

    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            displayRules(data);
            document.getElementById('errorMessage').style.display = 'none';
        })
        .catch(error => {
            document.getElementById('rulesTableBody').innerHTML = '';
            document.getElementById('prevPage').style.display = 'none';
            document.getElementById('nextPage').style.display = 'none';

            if (error instanceof SyntaxError || error instanceof TypeError) {
                console.log('Error:', error.message);
            } else {
                const errorMessage = `Error: ${error.message}`;
                document.getElementById('errorMessage').innerText = errorMessage;
                document.getElementById('errorMessage').style.display = 'block';
            }
        });
}

function displayRules(data) {
    const tableBody = document.getElementById('rulesTableBody');
    tableBody.innerHTML = '';

    data.results.forEach(event => {
        const row = `<tr>
            <td>${event.id}</td>
            <td>${event.gid}</td>
            <td>${event.sid}</td>
            <td>${event.rev}</td>
            <td>${event.action}</td>
            <td>${event.msg}</td>
        </tr>`;
        tableBody.insertAdjacentHTML('beforeend', row);
    });

    const prevPage = document.getElementById('prevPage');
    const nextPage = document.getElementById('nextPage');

    if (data.previous) {
        prevPage.innerHTML = `<a class="page-link" href="#" onclick="loadPrevPage(${currentPage - 1})">Previous page</a>`;
    } else {
        prevPage.innerHTML = '<span class="page-link disabled">Previous page</span>';
    }

    if (data.next) {
        nextPage.innerHTML = `<a class="page-link" href="#" onclick="loadNextPage(${currentPage + 1})">Next page</a>`;
    } else {
        nextPage.innerHTML = '<span class="page-link disabled">Next page</span>';
    }

    prevPage.style.display = 'block';
    nextPage.style.display = 'block';
}

function loadPrevPage() {
    if (currentPage > 1) {
        currentPage--;
        getSnortRules(false);
    }
}

function loadNextPage() {
    currentPage++;
    getSnortRules(false);
}

document.getElementById('dataForm').addEventListener('submit', function(event) {
    event.preventDefault();
    getSnortRules(true);
});


