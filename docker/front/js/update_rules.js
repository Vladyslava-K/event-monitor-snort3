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