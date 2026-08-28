const API_BASE = '';
let chart = null;

async function fetchData() {
    try {
        const [predRes, accRes, reportRes] = await Promise.all([
            fetch(`${API_BASE}/api/predict?symbol=NABIL&days=24`),
            fetch(`${API_BASE}/api/accuracy?symbol=NABIL`),
            fetch(`${API_BASE}/api/monthly_report?symbol=NABIL`)
        ]);

        const predData = await predRes.json();
        const accData = await accRes.json();
        const reportData = await reportRes.json();

        if (predData.success) displayPredictions(predData.data);
        if (accData.success) displayAccuracy(accData.data);
        if (reportData.success) displayReport(reportData.data);

        document.getElementById('last-updated').textContent = new Date().toLocaleString();
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('status').textContent = '🔴 Offline';
        document.getElementById('status').style.background = '#ff4444';
    }
}

function displayPredictions(data) {
    const predictions = data.predictions || [];
    const lastPrice = data.last_price || 794.33;

    document.getElementById('current-price').textContent = `₹${lastPrice.toFixed(2)}`;

    if (predictions.length > 0) {
        const predPrice = predictions[0].close || 0;
        document.getElementById('predicted-price').textContent = `₹${predPrice.toFixed(2)}`;

        const change = ((predPrice - lastPrice) / lastPrice * 100);
        const changeEl = document.getElementById('change');
        changeEl.textContent = `${change > 0 ? '+' : ''}${change.toFixed(2)}%`;
        changeEl.className = `stat-value ${change > 0 ? 'positive' : 'negative'}`;
    }

    let html = `<table>
        <thead><tr>
            <th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th>
        </tr></thead><tbody>`;

    predictions.slice(0, 24).forEach(p => {
        html += `<tr>
            <td>${p.date || '--'}</td>
            <td>${(p.open || 0).toFixed(2)}</td>
            <td>${(p.high || 0).toFixed(2)}</td>
            <td>${(p.low || 0).toFixed(2)}</td>
            <td><strong>${(p.close || 0).toFixed(2)}</strong></td>
            <td>${(p.volume || 0).toLocaleString()}</td>
        </tr>`;
    });

    html += `</tbody></table>`;
    document.getElementById('predictions-container').innerHTML = html;

    updateChart(predictions);
}

function displayAccuracy(data) {
    const dirAcc = data.direction_accuracy || 0;
    document.getElementById('accuracy').textContent = `${dirAcc.toFixed(1)}%`;
}

function displayReport(data) {
    const summary = data.summary || {};
    const recommendation = data.recommendation || 'Hold';

    let html = `
        <div class="dashboard">
            <div class="stat-card">
                <div class="stat-label">Month</div>
                <div class="stat-value">${data.month || '--'}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">MAE</div>
                <div class="stat-value">₹${(summary.mae || 0).toFixed(2)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">MAPE</div>
                <div class="stat-value">${(summary.mape || 0).toFixed(1)}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Direction Accuracy</div>
                <div class="stat-value">${(summary.direction_accuracy || 0).toFixed(1)}%</div>
            </div>
        </div>
        <div style="text-align: center; margin-top: 20px;">
            <span class="recommendation ${recommendation.toLowerCase()}">
                🎯 ${recommendation}
            </span>
        </div>
    `;

    document.getElementById('report-container').innerHTML = html;
}

function updateChart(predictions) {
    const ctx = document.getElementById('predictionChart').getContext('2d');
    
    if (chart) { chart.destroy(); }

    const labels = predictions.map(p => p.date || '');
    const openPrices = predictions.map(p => p.open || 0);
    const closePrices = predictions.map(p => p.close || 0);

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Open',
                    data: openPrices,
                    borderColor: '#00d4ff',
                    tension: 0.1
                },
                {
                    label: 'Close',
                    data: closePrices,
                    borderColor: '#00ff88',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#e0e0e0' } }
            },
            scales: {
                x: { ticks: { color: '#8899aa' } },
                y: { ticks: { color: '#8899aa' } }
            }
        }
    });
}

// Initial load
fetchData();
setInterval(fetchData, 300000);
