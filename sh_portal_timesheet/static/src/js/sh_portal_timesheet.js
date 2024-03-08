/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";

publicWidget.registry.sh_portal_timesheet = publicWidget.Widget.extend({
    selector: '.js_cls_create_view,.js_cls_create,.js_cls_edit_timesheet_btn,.js_cls_edit,.js_cls_del',
    events: {
        'click #create_timesheet': '_create_timesheet_view',
        'click #edit_timesheet': '_edit_timesheet_view',
        'click #add_timesheet': '_add_timesheet',
        'click #save_timesheet': '_save_timesheet',
        'click #delete_timesheet_from_list': '_del_timesheet_list',
        'click #delete_timesheet': '_del_timesheet',
        'change #project_id': '_product_onchange',
        'change #edit_project_id': '_edit_product',
    },
    _create_timesheet_view: function (e) {
        $.ajax({
            url: "/get-login-employee",
            data: {},
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                $('#employee_id').val(datas.employee_id);
            },
        });
        var today = new Date();
        var year = today.getFullYear();
        var month = (today.getMonth() + 1).toString().padStart(2, '0'); // Months are zero-based, so add 1
        var day = today.getDate().toString().padStart(2, '0');
        var formattedDate = year + '-' + month + '-' + day;
        $('#date').val(formattedDate);
        $('#ModalAdd').modal('show');
    },
    _edit_timesheet_view: function (e) {
        $('#edit_success_msg_div').addClass('o_hidden');
        var self = this;
        var $el = $(e.target).parents('tr').find("#timesheet_id").attr("value")
        var timesheet_id = parseInt($el)
        $.ajax({
            url: "/get-timesheet-data",
            data: { 'timesheet_id': timesheet_id },
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                var today = new Date(datas.edit_date);
                var year = today.getFullYear();
                var month = (today.getMonth() + 1).toString().padStart(2, '0'); // Months are zero-based, so add 1
                var day = today.getDate().toString().padStart(2, '0');
                var formattedDate = year + '-' + month + '-' + day;
                $('#edit_timesheet_id').val(timesheet_id);
                $('#edit_date').val(formattedDate);
                $('#edit_description').val(datas.edit_description);
                $('#edit_project_id').val(datas.edit_project_id);
                $('#edit_employee_id').val(datas.edit_employee_id);
                if (datas.edit_task_id) {
                    $('#edit_task_id').val(datas.edit_task_id);
                }
                if (datas.edit_duration) {
                    var decimalTimeString = datas.edit_duration;
                    var decimalTime = parseFloat(decimalTimeString);
                    decimalTime = decimalTime * 60 * 60;
                    var hours = Math.floor((decimalTime / (60 * 60)));
                    decimalTime = decimalTime - (hours * 60 * 60);
                    var minutes = Math.floor((decimalTime / 60));
                    decimalTime = decimalTime - (minutes * 60);
                    if (hours < 10) {
                        hours = "0" + hours;
                    }
                    if (minutes < 10) {
                        minutes = "0" + minutes;
                    }
                    var act_value = "" + hours + ":" + minutes;
                    $('#edit_duration').val(act_value);
                }
            },
        });
        $('#ModalEdit').modal('show');
    },
    _add_timesheet: function () {
        $('#success_msg_div').addClass('o_hidden');
        $.ajax({
            url: "/create-timesheet",
            data: {
                'name': $('#name').val(), 'date': $('#date').val(), 'project_id': $('#project_id').val(),
                'task_id': $('#task_id').val(), 'employee_id': $('#employee_id').val(), 'duration': $('#duration').val(),
            },
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                if (datas.msg) {

                    $('#error_msg_div').removeClass('o_hidden');
                    $('#success_msg_div').addClass('o_hidden');
                    $('#error_msg').html(datas.msg);
                }
                if (datas.success_msg) {
                    $('#error_msg_div').addClass('o_hidden');
                    $('#success_msg_div').removeClass('o_hidden');
                    $('#success_msg').html(datas.success_msg);
                    $('#name').val("");
                    $('#duration').val("");
                }
            },
        });
    },
    _save_timesheet: function () {
        $.ajax({
            url: "/edit-timesheet",
            data: {
                'edit_timesheet_id': $('#edit_timesheet_id').val(), 'edit_description': $('#edit_description').val(), 'edit_date': $('#edit_date').val(), 'edit_project_id': $('#edit_project_id').val(),
                'edit_task_id': $('#edit_task_id').val(), 'edit_employee_id': $('#edit_employee_id').val(), 'edit_duration': $('#edit_duration').val(),
            },
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                if (datas.success_msg) {
                    $('#edit_success_msg_div').removeClass('o_hidden');
                    $('#edit_success_msg').html(datas.success_msg);
                }
            },
        });
    },
    _del_timesheet_list: function (e) {
        var self = this;
        var $el = $(e.target).parents('tr').find("#timesheet_id").attr("value")
        var timesheet_id = parseInt($el)
        $('#delete_timesheet_id').val(timesheet_id);
        $('#delete_msg_div').addClass('o_hidden');
        $('#deleteModal').modal('show');
    },
    _product_onchange: function () {
        $.ajax({
            url: "/task-data",
            data: { 'project_id': $('#project_id').val() },
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                $('#task_id > option').remove();
                datas.task_list.forEach((rec) => {
                    $('#task_id').append(
                        '<option value="' + rec.id + '">' + rec.name + '</option>'
                    );
                });
            },
        });
    },
    _edit_product: function () {
        $.ajax({
            url: "/edit-get-task-data",
            data: { 'project_id': $('#edit_project_id').val() },
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                $('#edit_task_id > option').remove();
                datas.task_list.forEach((rec) => {
                    $('#edit_task_id').append(
                        '<option value="' + rec.id + '">' + rec.name + '</option>'
                    );
                });
            },
        });
    },
    _del_timesheet: function () {
        $.ajax({
            url: "/delete-timesheet-data",
            data: { 'timesheet_id': $('#delete_timesheet_id').val() },
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                if (datas.success_msg) {
                    location.reload(true);
                }
            },
        });
    },
});