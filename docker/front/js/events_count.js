function getEventsCount() {
    var period = document.getElementById("periodSelect").value;
    var type = document.getElementById("typeSelect").value;

    fetch('http://127.0.0.1:8000/api/v1/events/count?period=' + period + '&type=' + type, {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        displayEventsCount(data, type);
    })
    .catch((error) => {
        console.error('Error:', error);
        displayEventsCountError();
    });
}

function displayEventsCount(data, type) {
    var tableHeader = document.getElementById("eventsCountTableHeader");
    var tableBody = document.getElementById("eventsCountTableBody");

    tableHeader.innerHTML = ""; // Clear previous content
    tableBody.innerHTML = ""; // Clear previous content

    // Adjust table headers based on type
    var headerRow = tableHeader.insertRow(0);
    var headerCell1 = headerRow.insertCell(0);
    var headerCell2 = headerRow.insertCell(1);
    var headerCell3 = headerRow.insertCell(2);

    if (type === 'sid') {
        headerCell1.textContent = "SID";
    } else if (type === 'addr') {
        headerCell1.textContent = "Source Address";
        headerCell2.textContent = "Destination Address";
    }

    headerCell3.textContent = "Count";

    headerCell1.style.fontWeight = "bold";
    headerCell2.style.fontWeight = "bold";
    headerCell3.style.fontWeight = "bold";

    // Populate table rows
    data.forEach(function(item) {
        var row = tableBody.insertRow(tableBody.rows.length);
        var cell1 = row.insertCell(0);
        var cell2 = row.insertCell(1);
        var cell3 = row.insertCell(2);

        if (type === 'sid') {
            cell1.textContent = item.sid;
        } else if (type === 'addr') {
            cell1.textContent = item.src_addr;
            cell2.textContent = item.dst_addr;
        }

        cell3.textContent = item.count;
    });
}

function displayEventsCountError() {
    var tableBody = document.getElementById("eventsCountTableBody");
    tableBody.innerHTML = ""; // Clear previous content

    var row = tableBody.insertRow(tableBody.rows.length);
    var cell = row.insertCell(0);
    cell.textContent = "Error fetching events count. Please try again.";
}