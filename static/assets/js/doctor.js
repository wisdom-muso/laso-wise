$(document).ready(function () {
    // Initialize timepicker for existing fields
    $('.timepicker').timepicker({
        timeFormat: 'h:mm p',
        interval: 30,
        minTime: '00:00',
        maxTime: '23:30',
        defaultTime: '09:00',
        startTime: '00:00',
        dynamic: false,
        dropdown: true,
        scrollbar: true
    });

    $('.day_option').on('change', function () {
        let val = $(this).val();

        if ($(this).prop('checked')) {
            $('.hideable_' + val).slideDown();
        } else {
            $('.hideable_' + val).slideUp();
        }
    });

    $(".add_time_row").on('click', function (e) {
        e.preventDefault();

        let val = $(this).attr("data-id");
        $('.houritem_' + val).append(`
                <div class="row new_item_row_` + val + `">
                    <div class="col-sm-5 pr-0 mb-2">
                        <div class="input-group">
                            <div class="input-group-prepend">
                              <span class="input-group-text"><i class="fa fa-clock"></i></span>
                            </div>
                            <input type="text" class="form-control timepicker" name="start_time_` + val + `" value="" autocomplete="off">
                        </div>
                    </div>

                    <div class="col-sm-5 mb-2">
                        <div class="input-group">
                            <div class="input-group-prepend">
                              <span class="input-group-text"><i class="fa fa-clock"></i></span>
                            </div>
                            <input type="text" class="form-control timepicker" name="end_time_` + val + `" value="" autocomplete="off">
                        </div>
                    </div>

                    <div class="col-sm-2 mb-2 mt-2">
                        <a href="javascript:void(0);" class="remove_time_row text-danger"><i class="fa fa-trash"></i></a>
                    </div>
                </div>
            `);
            
        // Initialize timepicker for newly added fields
        $('.houritem_' + val + ' .timepicker').timepicker({
            timeFormat: 'h:mm p',
            interval: 30,
            minTime: '00:00',
            maxTime: '23:30',
            defaultTime: '09:00',
            startTime: '00:00',
            dynamic: false,
            dropdown: true,
            scrollbar: true
        });
    });

    $(".main_item").on('click', '.remove_time_row', function () {
        $(this).parent().parent().remove();
    });
    
    // Delete time row
    $(".del_time_row").on('click', function (e) {
        e.preventDefault();
        $(this).closest('.hour-item').remove();
    });
    
    // Form validation
    $(".validate-form").on('submit', function(e) {
        let valid = true;
        
        // Check if at least one day is selected
        if ($('.day_option:checked').length === 0) {
            alert('Please select at least one day for your schedule.');
            valid = false;
        }
        
        // Check if time slots are valid
        $('.day_option:checked').each(function() {
            let dayId = $(this).val();
            let startTimes = $('input[name="start_time_' + dayId + '"]');
            let endTimes = $('input[name="end_time_' + dayId + '"]');
            
            if (startTimes.length === 0) {
                alert('Please add at least one time slot for each selected day.');
                valid = false;
                return false;
            }
            
            for (let i = 0; i < startTimes.length; i++) {
                if ($(startTimes[i]).val() === '' || $(endTimes[i]).val() === '') {
                    alert('Please fill in all time slots.');
                    valid = false;
                    return false;
                }
            }
        });
        
        return valid;
    });
});