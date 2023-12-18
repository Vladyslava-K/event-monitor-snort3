let currentPage = 1;

function getSnortEvents() {
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
        $('#prevPage').html(`<a class="page-link" href="#" onclick="loadPage(${currentPage - 1})">Previous page</a>`);
    } else {
        $('#prevPage').html('<span class="page-link disabled">Previous page</span>');
    }

    if (data.next) {
        $('#nextPage').html(`<a class="page-link" href="#" onclick="loadPage(${currentPage + 1})">Next page</a>`);
    } else {
        $('#nextPage').html('<span class="page-link disabled">Next page</span>');
    }
}

function loadPage(page) {
    currentPage = page;
    getSnortEvents();
}

$('#dataForm').submit(function(event) {
    event.preventDefault();
    getSnortEvents();
});
