$(function () {
    $('.js-data-row-active').each(function (i, elem) {
        $(elem).addClass('info');

        var task_id = $(elem).data('id');
        var timerId = setInterval(function () {
                updateTask(task_id, timerId)
            }
            , 1000);
    })
    /*
     $('.js-data-row').on('click', function () {
     $('.js-data-row').removeClass('success');
     $(this).addClass('success');

     var task_id = $(this).data('id');

     var timerId = setInterval(function () {
     updateTask(task_id,timerId)
     }
     , 1000);

     $(this).data('timer',timerId);
     })*/

    function updateTask(task_id, timerId) {
        var url = '/check/' + task_id;
        var cur_row = $('.js-data-row[data-id="' + task_id + '"]');
        $.ajax({
            url: url,
            dataType: 'json',
            success: function (result) {
                cur_row.find('.js-task-state').html(result.STATE)
                cur_row.find('.js-task-count').html(result.COUNT)
                cur_row.find('.js-task-weight').html(result.WEIGHT)

                if (result.STATE == 'SUCCESS' || result.STATE == 'FAILURE'){
                    clearInterval(timerId);
                    cur_row.removeClass('info');

                    if (result.STATE == 'SUCCESS')
                        cur_row.addClass('success');
                    else
                        cur_row.addClass('danger');
                }


            }
        })
    }
})