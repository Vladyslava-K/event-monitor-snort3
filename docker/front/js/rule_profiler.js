function startProfiling() {
    var time = document.getElementById("timeInput").value;
    var until = document.getElementById("untilInput").value;

    var url = 'http://127.0.0.1:8000/api/v1/rule-profiler?';

    if (time) {
        url += 'time=' + time;
        var endTimestamp = Date.now() + (parseInt(time) * 60 * 1000);
    } else if (until) {
        url += 'until=' + until;
        var untilTime = new Date(until);
        var endTimestamp = untilTime.getTime();
    } else {
        alert("Please provide either 'time' or 'until' parameter.");
        return;
    }

    // Set the end timestamp in localStorage for both cases
    localStorage.setItem("endTimestamp", endTimestamp.toString());

    // Start the countdown timer
    updateCountdown();

    fetch(url, { method: 'GET' })
        .then(response => response.json())
        .then(data => {
            document.getElementById("lastProfilerResult").innerHTML = JSON.stringify(data);
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById("lastProfilerResult").innerHTML = "Error starting profiling.";
        });
}

// Update the countdown timer every second
function updateCountdown() {
    var endTimestampStr = localStorage.getItem("endTimestamp");

    if (endTimestampStr) {
        var endTimestamp = parseInt(endTimestampStr);

        var intervalId = setInterval(function () {
            var now = Date.now();
            var timeLeft = Math.max(0, Math.ceil((endTimestamp - now) / 1000));

            var minutes = Math.floor(timeLeft / 60);
            var seconds = timeLeft % 60;

            document.getElementById("countdownTimer").innerText = "Time Left: " + minutes + "m " + seconds + "s";

            if (timeLeft <= 0) {
                clearInterval(intervalId);
                document.getElementById("countdownTimer").innerText = "Rule profiling is stopped.";
            }
        }, 1000);
    }
}

// Fetch and display the last Rule Profiler result when the page loads
fetch('http://127.0.0.1:8000/api/v1/rule-profiler-last', { method: 'GET' })
    .then(response => response.json())
    .then(data => {
        var result = data.result;
        var output = 'Start Time: ' + result.startTime + '<br>';
        output += 'End Time: ' + result.endTime + '<br>';

        if (result.rules && result.rules.length > 0) {
            output += '<h5>Rules:</h5>';
            output += '<table class="table table-bordered">';
            output += '<thead><tr><th>GID</th><th>SID</th><th>Rev</th><th>Checks</th><th>Matches</th><th>Alerts</th><th>Time (us)</th><th>Avg Check</th><th>Avg Match</th><th>Avg Non-Match</th><th>Timeouts</th><th>Suspends</th><th>Rule Time Percentage</th></tr></thead>';
            output += '<tbody>';
            result.rules.forEach(rule => {
                output += '<tr>';
                output += '<td>' + rule.gid + '</td>';
                output += '<td>' + rule.sid + '</td>';
                output += '<td>' + rule.rev + '</td>';
                output += '<td>' + rule.checks + '</td>';
                output += '<td>' + rule.matches + '</td>';
                output += '<td>' + rule.alerts + '</td>';
                output += '<td>' + rule.timeUs + '</td>';
                output += '<td>' + rule.avgCheck + '</td>';
                output += '<td>' + rule.avgMatch + '</td>';
                output += '<td>' + rule.avgNonMatch + '</td>';
                output += '<td>' + rule.timeouts + '</td>';
                output += '<td>' + rule.suspends + '</td>';
                output += '<td>' + rule.ruleTimePercentage + '</td>';
                output += '</tr>';
            });
            output += '</tbody>';
            output += '</table>';
        }

        document.getElementById("lastProfilerResult").innerHTML = output;
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById("lastProfilerResult").innerHTML = "Error fetching last profiler result.";
    });

// Initial update of the countdown timer
updateCountdown();
