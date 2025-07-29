odoo.define('custom_website.auth_signup', function (require) {
    'use strict';

    var ajax = require('web.ajax');

    $(document).ready(function () {
        $('.oe_signup_form #get_otp').on('click', function () {
            var phone = $('#phone').val();
            ajax.jsonRpc('/web/signup/get_otp', 'call', {'phone': phone}).then(function (result) {
                if (result.status === 'success') {
                    console.log(result.otp);
                    alert(result.message);
                } else {
                    alert(result.message);
                }
            });
        });

        $('.oe_signup_form #phone').on('input', function () {
            $(this).val($(this).val().replace(/\D/g, ''));
        });

        $('.oe_signup_form #otp').on('input', function () {
            $(this).val($(this).val().replace(/\D/g, ''));
        });

        $('.oe_signup_form button.btn-primary').prop('disabled', true);
        $('.oe_signup_form #tnc').on('change', function () {
            $('.oe_signup_form button.btn-primary').prop('disabled', !this.checked);
        });

        ajax.jsonRpc('/get_provinces', 'call', {}).then(function(data){
            var provinceSelect = $('.oe_signup_form #city');
            $.each(data, function(index, item){
                provinceSelect.append(
                    $('<option>', {value: item.id, text: item.name})
                );
            });
        });

        $('.oe_signup_form #city').on('change', function(){
            var province_name = $(this).val();
            var citySelect = $('.oe_signup_form #district');
            citySelect.empty().append('<option value="">Select district</option>');
            if (province_name) {
                ajax.jsonRpc('/get_city_districts', 'call', {province_name: province_name}).then(function(data){
                    $.each(data, function(index, item){
                        citySelect.append(
                            $('<option>', {value: item.id, text: item.name})
                        );
                    });
                });
            }
        });
    });
});