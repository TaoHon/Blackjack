// updateDiagram.js
const socket = new WebSocket('ws://127.0.0.1:7999/ws/result/publish_results');

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    updateDiagram(data);
};


let myChart; // Holds the chart instance

function initChart() {
    const ctx = document.getElementById('resultsDiagram').getContext('2d');
    myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [], // Rounds will be added here
            datasets: [] // One dataset per player will be added dynamically
        },
        options: {
            animation: {
                duration: 0 // Disable animations by setting duration to 0
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Balance'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Round'
                    }
                }
            }
        }
    });
}


function updateDiagram(data) {
    // Example data format: { round: 1, balances: { 'Alice': 100, 'Bob': 95, 'Charlie': 105 } }
    const round = data.round;
    const balances = data.balances;

    // Update chart labels with new round
    myChart.data.labels.push(`Round ${round}`);

    // Update or create dataset for each player
    Object.keys(balances).forEach(playerName => {
        const balance = balances[playerName];
        let dataset = myChart.data.datasets.find(ds => ds.label === playerName);

        if (!dataset) {
            // Create new dataset for new player
            dataset = {
                label: playerName,
                data: [],
                fill: false,
                borderColor: getRandomColor(), // Assign a unique color or predefined color
                tension: 0.1
            };
            myChart.data.datasets.push(dataset);
        }

        // Append new balance data
        dataset.data.push(balance);
    });

    myChart.update();
}

function getRandomColor() {
    // A function to generate a random color for new datasets
    const r = Math.floor(Math.random() * 255);
    const g = Math.floor(Math.random() * 255);
    const b = Math.floor(Math.random() * 255);
    return `rgb(${r}, ${g}, ${b})`;
}

// Initial chart setup
initChart();
