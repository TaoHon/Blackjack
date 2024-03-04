const socket = new WebSocket('ws://127.0.0.1:7999/ws/result/publish_results');

let balanceChart, winRateChart;
let winHistory = {}; // Tracks wins, total rounds, and balance history for each player

function initCharts() {
    const balanceCtx = document.getElementById('resultsDiagram').getContext('2d');
    balanceChart = new Chart(balanceCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            animation: {duration: 0},
            scales: {
                y: {beginAtZero: false, title: {display: true, text: 'Balance'}},
                x: {title: {display: true, text: 'Round'}}
            }
        }
    });

    const winRateCtx = document.getElementById('winRateDiagram').getContext('2d');
    winRateChart = new Chart(winRateCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            animation: {duration: 0},
            scales: {
                y: {beginAtZero: true, title: {display: true, text: 'Win Rate (%)'}},
                x: {title: {display: true, text: 'Round'}}
            }
        }
    });
}

socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    updateCharts(data.round, data.balances);
};

function updateCharts(round, balances) {
    // Update balance chart
    balanceChart.data.labels.push(`Round ${round}`);
    Object.keys(balances).forEach(playerName => {
        let balanceDataset = balanceChart.data.datasets.find(ds => ds.label === playerName);
        if (!balanceDataset) {
            balanceDataset = {
                label: playerName,
                data: [],
                fill: false,
                borderColor: getRandomColor(),
                tension: 0.1
            };
            balanceChart.data.datasets.push(balanceDataset);
        }
        balanceDataset.data.push(balances[playerName]);
    });

    // Update win rate chart
    updateWinRateChart(round, balances);

    balanceChart.update();
    winRateChart.update();
}

function updateWinRateChart(round, balances) {
    Object.keys(balances).forEach(playerName => {
        if (!winHistory[playerName]) winHistory[playerName] = {wins: 0, total: 0, history: []};

        const playerHistory = winHistory[playerName];
        const lastBalance = playerHistory.history.slice(-1)[0] || balances[playerName];
        const currentBalance = balances[playerName];
        const win = currentBalance > lastBalance;

        playerHistory.wins += win ? 1 : 0;
        playerHistory.total++;
        playerHistory.history.push(currentBalance);
        if (playerHistory.history.length > 1000) playerHistory.history.shift();

        const winRate = (playerHistory.wins / playerHistory.total) * 100;
        let dataset = winRateChart.data.datasets.find(ds => ds.label === playerName);
        if (!dataset) {
            dataset = {
                label: playerName,
                data: [],
                fill: false,
                borderColor: getRandomColor(),
                tension: 0.1
            };
            winRateChart.data.datasets.push(dataset);
        }
        dataset.data.push(winRate);
    });

    while (winRateChart.data.labels.length < winRateChart.data.datasets[0].data.length) {
        winRateChart.data.labels.push(`Round ${round}`);
    }
}

function getRandomColor() {
    const r = Math.floor(Math.random() * 255);
    const g = Math.floor(Math.random() * 255);
    const b = Math.floor(Math.random() * 255);
    return `rgb(${r}, ${g}, ${b})`;
}

initCharts();
