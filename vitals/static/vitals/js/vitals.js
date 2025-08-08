// Vitals Tracking JavaScript

// Helper function to convert hex to rgb
function hexToRgb(hex) {
    // Remove # if present
    hex = hex.replace('#', '');
    
    // Convert 3-digit hex to 6-digits
    if (hex.length === 3) {
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    
    // Convert hex to rgb
    var r = parseInt(hex.substring(0, 2), 16);
    var g = parseInt(hex.substring(2, 4), 16);
    var b = parseInt(hex.substring(4, 6), 16);
    
    return r + ',' + g + ',' + b;
}

// Define normal range area plugin for Chart.js
const normalRangePlugin = {
    id: 'normalRange',
    beforeDraw: function(chart) {
        if (chart.config.options.normalRange) {
            var ctx = chart.ctx;
            var yAxis = chart.scales.y;
            var minNormal = chart.config.options.normalRange.min;
            var maxNormal = chart.config.options.normalRange.max;
            
            if (minNormal !== null && maxNormal !== null) {
                var yMin = yAxis.getPixelForValue(minNormal);
                var yMax = yAxis.getPixelForValue(maxNormal);
                var width = chart.width;
                var height = yMin - yMax;
                
                ctx.save();
                ctx.fillStyle = 'rgba(46, 204, 113, 0.1)';
                ctx.fillRect(0, yMax, width, height);
                ctx.restore();
            }
        }
    }
};

// Handle notification dismissal
$(document).ready(function() {
    // Handle notification dismissal
    $('.notification-dismiss').on('click', function() {
        var notificationId = $(this).data('id');
        $.post("/vitals/notifications/" + notificationId + "/read/", {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
        });
    });
    
    // Show/hide secondary value field based on category selection
    $('#id_category').on('change', function() {
        var categoryName = $(this).find('option:selected').text();
        
        if (categoryName.toLowerCase() === 'blood pressure') {
            $('.secondary-value-group').show();
        } else {
            $('.secondary-value-group').hide();
        }
    }).trigger('change');
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
});