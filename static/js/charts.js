// Charts functionality for the financial management system
let monthlyChart = null;
let categoryChart = null;

// Chart.js default configuration
Chart.defaults.font.family = 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif';
Chart.defaults.color = '#6c757d';

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if canvas elements exist
    const monthlyCanvas = document.getElementById('monthlyChart');
    const categoryCanvas = document.getElementById('categoryChart');
    
    if (monthlyCanvas) {
        initMonthlyChart();
    }
    
    if (categoryCanvas) {
        initCategoryChart();
    }
    
    // Initialize dashboard mini charts if they exist
    initDashboardCharts();
});

// Initialize monthly income vs expenses chart
function initMonthlyChart() {
    const ctx = document.getElementById('monthlyChart').getContext('2d');
    
    monthlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
            datasets: [{
                label: 'Receitas',
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Despesas',
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Receitas vs Despesas Mensais'
                },
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatCurrencyForChart(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrencyForChart(value);
                        }
                    }
                }
            }
        }
    });
}

// Initialize category expenses pie chart
function initCategoryChart() {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Gastos por Categoria'
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = formatCurrencyForChart(context.parsed);
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Initialize dashboard mini charts
function initDashboardCharts() {
    // Small trend charts for dashboard cards if needed
    const trendCanvases = document.querySelectorAll('.trend-chart');
    
    trendCanvases.forEach(canvas => {
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['', '', '', '', '', '', ''],
                datasets: [{
                    data: generateRandomTrend(),
                    borderColor: '#6a0dad',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: false
                    }
                },
                elements: {
                    point: {
                        radius: 0
                    }
                }
            }
        });
    });
}

// Update monthly chart with data from API
function updateMonthlyChart(ano) {
    if (!monthlyChart) return;
    
    fetch(`/api/receitas-despesas/${ano}`)
        .then(response => response.json())
        .then(data => {
            const receitas = data.map(item => item.receitas);
            const despesas = data.map(item => item.despesas);
            
            monthlyChart.data.datasets[0].data = receitas;
            monthlyChart.data.datasets[1].data = despesas;
            monthlyChart.update();
            
            // Update financial summary
            updateFinancialSummaryFromData(data);
            updateMonthlyBreakdown(data);
        })
        .catch(error => {
            console.error('Erro ao carregar dados do gráfico mensal:', error);
            showError('Erro ao carregar dados do gráfico mensal');
        });
}

// Update category chart with data from API
function updateCategoryChart(ano, mes) {
    if (!categoryChart) return;
    
    fetch(`/api/gastos-categoria/${ano}/${mes}`)
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.categoria);
            const values = data.map(item => item.valor);
            const colors = data.map(item => item.cor);
            
            categoryChart.data.labels = labels;
            categoryChart.data.datasets[0].data = values;
            categoryChart.data.datasets[0].backgroundColor = colors;
            categoryChart.update();
        })
        .catch(error => {
            console.error('Erro ao carregar dados do gráfico de categorias:', error);
            showError('Erro ao carregar dados do gráfico de categorias');
        });
}

// Update financial summary with data
function updateFinancialSummaryFromData(data) {
    const totalReceitas = data.reduce((sum, item) => sum + item.receitas, 0);
    const totalDespesas = data.reduce((sum, item) => sum + item.despesas, 0);
    const saldoAno = totalReceitas - totalDespesas;
    const mediaMensal = saldoAno / 12;
    
    const receitasElement = document.getElementById('total-receitas-ano');
    const despesasElement = document.getElementById('total-despesas-ano');
    const saldoElement = document.getElementById('saldo-ano');
    const mediaElement = document.getElementById('media-mensal');
    
    if (receitasElement) receitasElement.textContent = formatCurrencyForChart(totalReceitas);
    if (despesasElement) despesasElement.textContent = formatCurrencyForChart(totalDespesas);
    if (saldoElement) {
        saldoElement.textContent = formatCurrencyForChart(saldoAno);
        saldoElement.className = saldoAno >= 0 ? 'text-success' : 'text-danger';
    }
    if (mediaElement) mediaElement.textContent = formatCurrencyForChart(mediaMensal);
}

// Update monthly breakdown table
function updateMonthlyBreakdown(data) {
    const tbody = document.querySelector('#monthly-breakdown tbody');
    if (!tbody) return;
    
    const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                   'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
    
    tbody.innerHTML = '';
    
    data.forEach((item, index) => {
        const saldo = item.receitas - item.despesas;
        const economia = item.receitas > 0 ? ((saldo / item.receitas) * 100) : 0;
        
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${meses[index]}</td>
            <td class="text-success">${formatCurrencyForChart(item.receitas)}</td>
            <td class="text-danger">${formatCurrencyForChart(item.despesas)}</td>
            <td class="${saldo >= 0 ? 'text-success' : 'text-danger'}">${formatCurrencyForChart(saldo)}</td>
            <td class="${economia >= 20 ? 'text-success' : economia >= 10 ? 'text-warning' : 'text-danger'}">
                ${economia.toFixed(1)}%
            </td>
        `;
    });
}

// Update financial summary (alternative method for direct values)
function updateFinancialSummary(ano) {
    // This can be used as a fallback or for real-time updates
    const currentYear = new Date().getFullYear();
    if (ano != currentYear) {
        // For previous years, use API data
        updateMonthlyChart(ano);
    }
}

// Format currency for chart display
function formatCurrencyForChart(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

// Generate random trend data for demo purposes
function generateRandomTrend() {
    const data = [];
    let value = 50 + Math.random() * 50;
    
    for (let i = 0; i < 7; i++) {
        value += (Math.random() - 0.5) * 20;
        value = Math.max(0, Math.min(100, value));
        data.push(value);
    }
    
    return data;
}

// Export chart functions for external use
window.ChartFunctions = {
    updateMonthlyChart,
    updateCategoryChart,
    updateFinancialSummary,
    formatCurrencyForChart
};

// Chart color schemes
const chartColors = {
    primary: '#6a0dad',
    success: '#28a745',
    danger: '#dc3545',
    warning: '#ffc107',
    info: '#17a2b8',
    secondary: '#6c757d'
};

// Chart animation options
const chartAnimationOptions = {
    duration: 1000,
    easing: 'easeInOutQuart'
};

// Utility function to create gradient backgrounds
function createGradient(ctx, colorStart, colorEnd) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, colorStart);
    gradient.addColorStop(1, colorEnd);
    return gradient;
}

// Responsive chart configuration
function getResponsiveOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: chartAnimationOptions
    };
}

// Initialize budget progress charts
function initBudgetCharts() {
    const budgetCards = document.querySelectorAll('.budget-card');
    
    budgetCards.forEach(card => {
        const canvas = card.querySelector('canvas.budget-chart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const percentage = parseFloat(card.dataset.percentage || 0);
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [percentage, 100 - percentage],
                    backgroundColor: [
                        percentage >= 100 ? chartColors.danger : 
                        percentage >= 80 ? chartColors.warning : chartColors.success,
                        '#e9ecef'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                ...getResponsiveOptions(),
                plugins: {
                    legend: {
                        display: false
                    }
                },
                cutout: '70%'
            }
        });
    });
}

// Account balance trend charts
function initAccountTrendCharts() {
    const accountCards = document.querySelectorAll('.account-card canvas');
    
    accountCards.forEach(canvas => {
        const ctx = canvas.getContext('2d');
        const trendData = generateRandomTrend();
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array(trendData.length).fill(''),
                datasets: [{
                    data: trendData,
                    borderColor: chartColors.primary,
                    backgroundColor: createGradient(ctx, 
                        'rgba(106, 13, 173, 0.3)', 
                        'rgba(106, 13, 173, 0.05)'),
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2
                }]
            },
            options: {
                ...getResponsiveOptions(),
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: false
                    }
                }
            }
        });
    });
}

// Category spending trend over time
function createCategoryTrendChart(categoryId, canvasId) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // This would typically fetch data from an API
    const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'];
    const data = generateRandomTrend().slice(0, 6);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: months,
            datasets: [{
                label: 'Gastos',
                data: data,
                backgroundColor: chartColors.primary + '80',
                borderColor: chartColors.primary,
                borderWidth: 1
            }]
        },
        options: {
            ...getResponsiveOptions(),
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrencyForChart(value * 100);
                        }
                    }
                }
            }
        }
    });
}

// Initialize all chart types based on page content
function initAllCharts() {
    initBudgetCharts();
    initAccountTrendCharts();
    
    // Initialize specific charts based on page
    const currentPage = window.location.pathname;
    
    if (currentPage.includes('relatorios')) {
        // Charts are initialized by the reports page
    } else if (currentPage.includes('dashboard')) {
        initDashboardCharts();
    }
}

// Call initialization when DOM is ready
document.addEventListener('DOMContentLoaded', initAllCharts);

// Export for global access
window.Charts = {
    initMonthlyChart,
    initCategoryChart,
    updateMonthlyChart,
    updateCategoryChart,
    createCategoryTrendChart,
    chartColors,
    formatCurrencyForChart
};
