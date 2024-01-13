function executeCommand() {
    var command = document.getElementById("commandInput").value;

    fetch('http://127.0.0.1:8000/api/v1/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: command }),
    })
    .then(response => response.json())
    .then(data => {
        var formattedResponse = data.response.replace(/\n/g, '<br>'); // Convert newlines to HTML line breaks
        document.getElementById("responseOutput").innerHTML = "<code>" + formattedResponse + "</code>";
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}