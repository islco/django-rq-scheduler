(function($) {
    $(function() {
        var updateDisplayedFields = function(row) {
             const selectField = row.find('.field-arg_type select'),
                 strVal = row.find('.field-str_val'),
                 intVal = row.find('.field-int_val'),
                 boolVal = row.find('.field-bool_val'),
                 datetimeVal = row.find('.field-datetime_val');

             var showRow = function(selector) {
                 selector.show();
                 selector.find('label').addClass('required')
             };
             var hideRow = function(selector) {
                 selector.hide();
                 selector.find(':input').val('');
             };

             var toggleVerified = function(value) {
                value === 'str_val' ? showRow(strVal) : hideRow(strVal);
                value === 'int_val' ? showRow(intVal) : hideRow(intVal);
                value === 'bool_val' ? showRow(boolVal) : hideRow(boolVal);
                value === 'datetime_val' ? showRow(datetimeVal) : hideRow(datetimeVal);
             };
             toggleVerified(selectField.val());
             selectField.change(function() {
                toggleVerified($(this).val());
             });
        };

        $(document).on('formset:added', function (event, row, options) {
             updateDisplayedFields(row);
        });


        $('.dynamic-scheduler-jobkwarg-content_type-object_id, ' +
            '.dynamic-scheduler-jobarg-content_type-object_id').each(function() {
            updateDisplayedFields($(this));
        });
    });
})(django.jQuery);
