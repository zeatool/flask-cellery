 $(function () {
        $('.js-data-row').on('click', function () {
            $('.js-data-row').removeClass('success');
            $(this).addClass('success');

            var task_id = $(this).data('id');
            var url = '/check/' + task_id;
            $.ajax({
                url: url,
                dataType:'json',
                success: function (result) {
                    $('.js-task-state').html(result.STATE)
                    $('.js-task-count').html(result.COUNT)
                }
            })
        })
    })