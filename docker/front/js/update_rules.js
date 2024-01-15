function updateRules() {
    document.getElementById("updateRulesStatus").innerText = "Updating rules";
    var dots = 0;
    var intervalId = setInterval(function() {
        document.getElementById("updateRulesStatus").innerText += ".";
        dots++;
    }, 1000);

    fetch('http://127.0.0.1:8000/api/v1/update-rules', {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        clearInterval(intervalId);
        var formattedResponse = data.response.replace(/\n/g, '<br>');
        document.getElementById("updateRulesStatus").innerText = "Update complete!";
        document.getElementById("updateRulesResponse").innerHTML = "<code>" + formattedResponse + "</code>";
    })
    .catch((error) => {
        console.error('Error:', error);
        clearInterval(intervalId);
        document.getElementById("updateRulesStatus").innerText = "Update failed. Please try again.";
    });
}

function addRule() {
    var rule = document.getElementById("ruleInput").value;
    if (!rule) {
        alert("Please enter a rule.");
        return;
    }

    // Make a POST request to the API
    fetch('http://127.0.0.1:8000/api/v1/write-rule', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content: rule,
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Display response message
        var responseMessageDiv = document.getElementById("responseMessage");
        responseMessageDiv.innerHTML = data.success ?
            `<div class="alert alert-success">${data.message}</div>` :
            `<div class="alert alert-danger">${data.message}</div>`;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}