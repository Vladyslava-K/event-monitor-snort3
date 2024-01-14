$(document).ready(function(){
    // Clear date inputs when the page loads
    $('#periodStart, #periodEnd').val('');

    // Event listener for fetching performance data
    $('#getPerfDataBtn').on('click', function() {
        getPerfData();
    });
});

function getPerfData() {
    var startDate = $('#periodStart').val();
    var endDate = $('#periodEnd').val();
    var aggr = $('#aggrSelect').val();
    var prefix = $('#prefixInput').val();

    // Check if both start and end dates are provided
    if (startDate && endDate) {
        // Construct query string
        var queryString = new URLSearchParams({
            begin: startDate,
            end: endDate,
            aggr: aggr,
            prefix: prefix
        });

        fetch('http://127.0.0.1:8000/api/v1/perf-monitor?' + queryString, {
            method: 'GET',
        })
        .then(response => response.json())
        .then(data => {
            displayPerfData(data.response);
        })
        .catch((error) => {
            console.error('Error:', error);
            displayPerfDataError();
        });
    } else {
        // Display an error message if start or end date is missing
        displayPerfDataError("Please provide both start and end dates.");
    }
}

function displayPerfData(data) {
    var perfDataResponse = document.getElementById("perfDataResponse");
    perfDataResponse.textContent = ""; // Clear previous content

    if (Array.isArray(data)) {
        // Display each document as a new line
        data.forEach(function(document) {
            perfDataResponse.textContent += JSON.stringify(document, null, 2) + '\n';
        });
    } else {
        // Display key-value pairs as separate lines
        for (var key in data) {
            perfDataResponse.textContent += key + ': ' + JSON.stringify(data[key], null, 2) + '\n';
        }
    }
}

function displayPerfDataError(message) {
    var perfDataResponse = document.getElementById("perfDataResponse");
    perfDataResponse.textContent = message || "Error fetching performance data. Please try again.";
}