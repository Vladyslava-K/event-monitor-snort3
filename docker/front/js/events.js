let currentPage = 1;

document.addEventListener('DOMContentLoaded', function() {
    getSnortEvents();
});

function getSnortEvents(newSearch = true) {
    if (newSearch) {
        currentPage = 1;
    }

    const sid = $('#sid').val();
    const sourceIp = $('#source_ip').val();
    const destIp = $('#dest_ip').val();
    const sourcePort = $('#source_port').val();
    const destPort = $('#dest_port').val();
    const protocol = $('#protocol').val();

    const requestData = {
        page: currentPage,
    };

    if (sid.trim() !== '') {
        requestData.sid = sid.trim();
    }

    if (sourceIp.trim() !== '') {
        requestData.source_ip = sourceIp.trim();
    }

    if (destIp.trim() !== '') {
        requestData.dest_ip = destIp.trim();
    }

    if (sourcePort.trim() !== '') {
        requestData.source_port = sourcePort.trim();
    }

    if (destPort.trim() !== '') {
        requestData.dest_port = destPort.trim();
    }

    if (protocol.trim() !== '') {
        requestData.protocol = protocol.trim();
    }

    $.ajax({
        url: 'http://127.0.0.1:8000/api/v1/events',
        type: 'GET',
        data: requestData,
        success: function(data) {
            displayEvents(data);
            $('#errorMessage').hide();
            $('#updateMessage').hide();
        },
        error: function(xhr, textStatus, errorThrown) {
            $('#eventsTableBody').empty();
            $('#prevPage, #nextPage').hide();

            if (xhr.status === 400) {
                const errorResponse = JSON.parse(xhr.responseText);
                const errorMessage = errorResponse.message;
                $('#errorMessage').text(`Error: ${errorMessage}`).show();
            } else {
                console.log('Error:', errorThrown);
            }
        }
    });
}

function displayEvents(data) {
    const tableBody = $('#eventsTableBody');
    tableBody.empty();

    $.each(data.results, function(index, event) {
        const row = `<tr>
            <td>${event.id}</td>
            <td>${event.sid}</td>
            <td>${event.timestamp}</td>
            <td>${event.src_addr}</td>
            <td>${event.src_port}</td>
            <td>${event.dst_addr}</td>
            <td>${event.dst_port}</td>
            <td>${event.proto}</td>
            <td>${event.action}</td>
            <td>${event.msg}</td>
        </tr>`;
        tableBody.append(row);
    });

    if (data.previous) {
        $('#prevPage').html(`<a class="page-link" href="#" onclick="loadPrevPage(${currentPage - 1})">Previous page</a>`);
    } else {
        $('#prevPage').html('<span class="page-link disabled">Previous page</span>');
    }

    if (data.next) {
        $('#nextPage').html(`<a class="page-link" href="#" onclick="loadNextPage(${currentPage + 1})">Next page</a>`);
    } else {
        $('#nextPage').html('<span class="page-link disabled">Next page</span>');
    }
}

function loadPrevPage() {
    if (currentPage > 1) {
        currentPage--;
        getSnortEvents(false);
    }
}

function loadNextPage() {
    currentPage++;
    getSnortEvents(false);
}

$('#dataForm').submit(function(event) {
    event.preventDefault();
    getSnortEvents(true);
});

function deleteEvents() {
    const patchData = {
    };

    $.ajax({
        url: 'http://127.0.0.1:8000/api/v1/events',
        type: 'PATCH',
        data: JSON.stringify(patchData),
        contentType: 'application/json',
        success: function(response) {
            // handle success
            $('#errorMessage').hide();
            console.log('Patch successful', response);
            $('#updateMessage').text('Delete successful!').show();
        },

        error: function(xhr, textStatus, errorThrown) {
            const errorResponse = JSON.parse(xhr.responseText);
            const errorMessage = errorResponse.message;
            $('#errorMessage').text(`Error: ${errorMessage}`).show();
            console.error('Patch error', errorThrown);
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    getSnortEvents();
    document.getElementById('deleteButton').addEventListener('click', deleteEvents);
});