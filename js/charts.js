// Chart configurations for Warrior Poets Fantasy Football
// Uses Chart.js library

// Color palette - Vibrant & Fun
const chartColors = {
  primary: '#ff6b6b',
  secondary: '#4ecdc4',
  gold: '#f9a825',
  blue: '#5c7cfa',
  purple: '#9775fa',
  orange: '#ff922b',
  teal: '#20c997',
  pink: '#f06595',
  grey: '#868e96',

  // For member-specific colors - more vibrant
  members: {
    'Andrew': '#ff6b6b',
    'Ben': '#51cf66',
    'CP': '#5c7cfa',
    'Dues': '#9775fa',
    'Farber': '#ff922b',
    'JB': '#20c997',
    'Jett': '#f06595',
    'Lloyd': '#fcc419',
    'Pinkston': '#22b8cf',
    'Rich': '#94d82d',
    'Rick': '#ff8787',
    'Rizzo': '#748ffc',
    'Stern': '#69db7c',
    'Yonk': '#e599f7',
    'Heath': '#868e96',
    'Jerome': '#adb5bd',
    'Marty': '#ced4da',
    'Woock': '#dee2e6'
  }
};

// Default chart options for light theme
const defaultOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: '#5a5a7a',
        font: {
          family: "'Inter', sans-serif"
        }
      }
    },
    tooltip: {
      backgroundColor: '#ffffff',
      titleColor: '#1a1a2e',
      bodyColor: '#5a5a7a',
      borderColor: '#e0e4ed',
      borderWidth: 1,
      cornerRadius: 8,
      titleFont: {
        family: "'Inter', sans-serif",
        weight: 600
      },
      bodyFont: {
        family: "'Inter', sans-serif"
      }
    }
  },
  scales: {
    x: {
      grid: {
        color: '#e0e4ed',
        drawBorder: false
      },
      ticks: {
        color: '#5a5a7a',
        font: {
          family: "'Inter', sans-serif"
        }
      }
    },
    y: {
      grid: {
        color: '#e0e4ed',
        drawBorder: false
      },
      ticks: {
        color: '#5a5a7a',
        font: {
          family: "'Inter', sans-serif"
        }
      }
    }
  }
};

// Create a line chart for points over time
function createPointsLineChart(canvasId, data, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const config = {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: data.datasets.map((ds, i) => ({
        label: ds.label,
        data: ds.data,
        borderColor: ds.color || chartColors.members[ds.label] || chartColors.primary,
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
        tension: 0.3,
        ...ds
      }))
    },
    options: {
      ...defaultOptions,
      ...options,
      plugins: {
        ...defaultOptions.plugins,
        ...options.plugins,
        legend: {
          ...defaultOptions.plugins.legend,
          position: 'bottom'
        }
      }
    }
  };

  return new Chart(ctx, config);
}

// Create a bar chart for rankings
function createBarChart(canvasId, data, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const config = {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: data.label || 'Value',
        data: data.values,
        backgroundColor: data.colors || data.values.map((v, i) => {
          if (i === 0) return chartColors.gold;
          if (i === 1) return '#c0c0c0';
          if (i === 2) return '#cd7f32';
          return chartColors.primary;
        }),
        borderColor: 'transparent',
        borderRadius: 4,
        barThickness: options.barThickness || 'flex'
      }]
    },
    options: {
      ...defaultOptions,
      ...options,
      indexAxis: options.horizontal ? 'y' : 'x',
      plugins: {
        ...defaultOptions.plugins,
        legend: {
          display: false
        }
      }
    }
  };

  return new Chart(ctx, config);
}

// Create a cumulative line chart for sidebets
function createCumulativeChart(canvasId, data, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  // Convert weekly data to cumulative
  const cumulativeDatasets = data.datasets.map(ds => {
    let cumulative = 0;
    const cumulativeData = ds.data.map(val => {
      if (val !== null && val !== undefined) {
        cumulative += val;
      }
      return cumulative;
    });
    return {
      ...ds,
      data: cumulativeData
    };
  });

  return createPointsLineChart(canvasId, {
    labels: data.labels,
    datasets: cumulativeDatasets
  }, {
    ...options,
    scales: {
      ...defaultOptions.scales,
      y: {
        ...defaultOptions.scales.y,
        ticks: {
          ...defaultOptions.scales.y.ticks,
          callback: (value) => value >= 0 ? `+${value}` : value
        }
      }
    }
  });
}

// Create a small sparkline chart (no axes, minimal)
function createSparkline(canvasId, data, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const config = {
    type: 'line',
    data: {
      labels: data.map((_, i) => i),
      datasets: [{
        data: data,
        borderColor: options.color || chartColors.primary,
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false }
      },
      scales: {
        x: { display: false },
        y: { display: false }
      }
    }
  };

  return new Chart(ctx, config);
}

// Create a doughnut chart for championship distribution
function createDoughnutChart(canvasId, data, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const config = {
    type: 'doughnut',
    data: {
      labels: data.labels,
      datasets: [{
        data: data.values,
        backgroundColor: data.labels.map(label => chartColors.members[label] || chartColors.primary),
        borderColor: '#ffffff',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            color: '#5a5a7a',
            padding: 16,
            font: {
              family: "'Inter', sans-serif"
            }
          }
        },
        tooltip: {
          ...defaultOptions.plugins.tooltip,
          callbacks: {
            label: (context) => {
              return `${context.label}: ${context.raw} championship${context.raw > 1 ? 's' : ''}`;
            }
          }
        }
      }
    }
  };

  return new Chart(ctx, config);
}

// Create weekly performance heatmap (simplified as a grid)
function createWeeklyHeatmap(containerId, data, options = {}) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const { weeks, members, values, minVal, maxVal } = data;

  // Color scale function - vibrant colors for light theme
  const getColor = (val) => {
    if (val === null || val === undefined) return '#f0f2f7';
    const ratio = (val - minVal) / (maxVal - minVal);
    if (ratio > 0.75) return '#51cf66';
    if (ratio > 0.5) return '#94d82d';
    if (ratio > 0.25) return '#fcc419';
    return '#ff6b6b';
  };

  let html = `
    <div class="heatmap">
      <div class="heatmap-header">
        <div class="heatmap-cell heatmap-label"></div>
        ${weeks.map(w => `<div class="heatmap-cell heatmap-header-cell">${w}</div>`).join('')}
      </div>
      ${members.map((member, i) => `
        <div class="heatmap-row">
          <div class="heatmap-cell heatmap-label">${member}</div>
          ${values[i].map(val => `
            <div class="heatmap-cell" style="background-color: ${getColor(val)}" title="${member} Week ${weeks[values[i].indexOf(val)]}: ${val ? val.toFixed(1) : '—'}">
            </div>
          `).join('')}
        </div>
      `).join('')}
    </div>
    <style>
      .heatmap { display: flex; flex-direction: column; gap: 2px; }
      .heatmap-header, .heatmap-row { display: flex; gap: 2px; }
      .heatmap-cell {
        width: 30px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        border-radius: 4px;
      }
      .heatmap-label {
        width: 80px;
        justify-content: flex-start;
        color: #5a5a7a;
        font-size: 0.8rem;
      }
      .heatmap-header-cell {
        background-color: #f0f2f7;
        color: #5a5a7a;
        font-size: 0.7rem;
      }
    </style>
  `;

  container.innerHTML = html;
}

// Export
window.WPCharts = {
  colors: chartColors,
  createPointsLineChart,
  createBarChart,
  createCumulativeChart,
  createSparkline,
  createDoughnutChart,
  createWeeklyHeatmap
};
