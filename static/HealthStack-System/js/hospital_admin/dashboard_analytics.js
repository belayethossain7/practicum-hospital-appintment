(function () {
    function buildLineChart(ctx, labels, data) {
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Appointments',
                    data: data,
                    borderColor: '#0f6e8c',
                    backgroundColor: 'rgba(58, 160, 181, 0.18)',
                    fill: true,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: '#0f6e8c',
                    tension: 0.35
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: {
                    display: false
                },
                scales: {
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
                            precision: 0
                        },
                        gridLines: {
                            color: 'rgba(219, 231, 240, 0.8)'
                        }
                    }],
                    xAxes: [{
                        gridLines: {
                            display: false
                        }
                    }]
                }
            }
        });
    }

    function buildDoughnutChart(ctx, labels, data) {
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    borderWidth: 0,
                    backgroundColor: ['#0f6e8c', '#3aa0b5', '#1f9d70', '#d48b1f']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12
                    }
                },
                cutoutPercentage: 62
            }
        });
    }

    function buildBarChart(ctx, labels, data) {
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: ['#0f6e8c', '#3aa0b5', '#1f9d70', '#d48b1f']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: {
                    display: false
                },
                scales: {
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
                            precision: 0
                        },
                        gridLines: {
                            color: 'rgba(219, 231, 240, 0.8)'
                        }
                    }],
                    xAxes: [{
                        gridLines: {
                            display: false
                        }
                    }]
                }
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        if (typeof Chart === 'undefined' || !window.haDashboardConfig) {
            return;
        }

        var config = window.haDashboardConfig;
        var appointmentCanvas = document.getElementById('haAppointmentChart');
        var mixCanvas = document.getElementById('haEntityMixChart');
        var totalsCanvas = document.getElementById('haEntityTotalsChart');

        if (appointmentCanvas) {
            buildLineChart(appointmentCanvas.getContext('2d'), config.weekLabels, config.weekCounts);
        }
        if (mixCanvas) {
            buildDoughnutChart(mixCanvas.getContext('2d'), config.entityLabels, config.entityCounts);
        }
        if (totalsCanvas) {
            buildBarChart(totalsCanvas.getContext('2d'), config.entityLabels, config.entityCounts);
        }
    });
})();
