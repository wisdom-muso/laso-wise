/**
 * Sync Monitor JavaScript
 */

// Real-time updates for system health and sync status
function updateRealTimeData(healthApiUrl) {
    $.ajax({
        url: healthApiUrl,
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            // Update component health status
            for (var component in data.components) {
                var componentData = data.components[component];
                var statusClass = 'status-' + componentData.status;
                
                // Update status indicator
                $('.component-card h5:contains("' + component.charAt(0).toUpperCase() + component.slice(1) + '") .status-indicator')
                    .removeClass('status-healthy status-warning status-critical status-unknown')
                    .addClass(statusClass);
                
                // Update status text
                $('.component-card h5:contains("' + component.charAt(0).toUpperCase() + component.slice(1) + '")')
                    .closest('.card-header')
                    .next('.card-body')
                    .find('.text-healthy, .text-warning, .text-critical, .text-unknown')
                    .removeClass('text-healthy text-warning text-critical text-unknown')
                    .addClass('text-' + componentData.status)
                    .text(componentData.status.charAt(0).toUpperCase() + componentData.status.slice(1));
                
                // Update response time
                $('.component-card h5:contains("' + component.charAt(0).toUpperCase() + component.slice(1) + '")')
                    .closest('.card-header')
                    .next('.card-body')
                    .find('span:contains("Response Time")')
                    .next('span')
                    .text(componentData.response_time.toFixed(2) + ' ms');
                
                // Update last check time
                $('.component-card h5:contains("' + component.charAt(0).toUpperCase() + component.slice(1) + '")')
                    .closest('.card-header')
                    .next('.card-body')
                    .find('span:contains("Last Check")')
                    .next('span')
                    .text(formatDateTime(componentData.checked_at));
                
                // Update details
                if (componentData.details) {
                    $('.component-card h5:contains("' + component.charAt(0).toUpperCase() + component.slice(1) + '")')
                        .closest('.card-header')
                        .next('.card-body')
                        .find('small.text-muted')
                        .text(componentData.details);
                }
            }
            
            // Update in-progress syncs
            updateInProgressSyncs(data.in_progress_syncs);
        },
        complete: function() {
            // Schedule the next update
            setTimeout(function() {
                updateRealTimeData(healthApiUrl);
            }, 10000); // Update every 10 seconds
        }
    });
}

// Update in-progress sync operations
function updateInProgressSyncs(inProgressSyncs) {
    // This would be implemented in a real application
    // For now, we'll just update the count
    $('.sync-stats-card .stat-value:contains("In Progress")').text(inProgressSyncs.length);
}

// Format date and time
function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return 'Never';
    
    var date = new Date(dateTimeStr);
    var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    var month = months[date.getMonth()];
    var day = date.getDate();
    var year = date.getFullYear();
    var hours = date.getHours().toString().padStart(2, '0');
    var minutes = date.getMinutes().toString().padStart(2, '0');
    
    return month + ' ' + day + ', ' + year + ' ' + hours + ':' + minutes;
}

// Initialize sync history chart
function initSyncHistoryChart(chartData) {
    var ctx = document.getElementById('syncHistoryChart').getContext('2d');
    
    var syncHistoryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: 'Completed',
                    data: chartData.completed,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Failed',
                    data: chartData.failed,
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                    borderColor: 'rgba(220, 53, 69, 1)',
                    borderWidth: 1
                },
                {
                    label: 'In Progress',
                    data: chartData.in_progress,
                    backgroundColor: 'rgba(0, 123, 255, 0.7)',
                    borderColor: 'rgba(0, 123, 255, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Pending',
                    data: chartData.pending,
                    backgroundColor: 'rgba(23, 162, 184, 0.7)',
                    borderColor: 'rgba(23, 162, 184, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
    
    return syncHistoryChart;
}

// Initialize entity statistics chart
function initEntityChart(entityLabels, successData, failureData) {
    var ctx = document.getElementById('entityChart').getContext('2d');
    
    var entityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: entityLabels,
            datasets: [
                {
                    label: 'Success',
                    data: successData,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Failed',
                    data: failureData,
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                    borderColor: 'rgba(220, 53, 69, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
    
    return entityChart;
}