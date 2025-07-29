// fetch('https://api.allorigins.win/get?url=' + encodeURIComponent('https://provinces.open-api.vn/api/'))
//     .then(response => response.json())
//     .then(data => { 
//         const provinces = JSON.parse(data.contents);
//         const provinceSender = document.getElementById('province_sender');
//         const provinceReceiver = document.getElementById('province_receiver');
//         const districtSender = document.getElementById('district_sender');
//         const districtReceiver = document.getElementById('district_receiver');

//         provinces.forEach(province => {
//             const optionSender = document.createElement('option');
//             optionSender.value = province.code; 
//             optionSender.textContent = province.name; 
//             provinceSender.appendChild(optionSender);
            
//             const optionReceiver = document.createElement('option');
//             optionReceiver.value = province.code;
//             optionReceiver.textContent = province.name; 
//             provinceReceiver.appendChild(optionReceiver);
//         });

//         provinceSender.addEventListener('change', function() {
//             fetchDistricts(provinceSender.value, districtSender);
//         });

//         provinceReceiver.addEventListener('change', function() {
//             fetchDistricts(provinceReceiver.value, districtReceiver);
//         });
//     })
//     .catch(error => {
//         console.error('Error fetching provinces:', error);
//     });

// function fetchDistricts(provinceCode, districtElement) {
//     fetch('https://api.allorigins.win/get?url=' + encodeURIComponent(`https://provinces.open-api.vn/api/p/${provinceCode}?depth=2`))
//         .then(response => response.json())
//         .then(data => {
//             const province = JSON.parse(data.contents);
//             const districts = province.districts;

//             districtElement.innerHTML = '<option value="">Select district</option>';

//             districts.forEach(district => {
//                 const option = document.createElement('option');
//                 option.value = district.code;
//                 option.textContent = district.name;
//                 districtElement.appendChild(option);
//             });
//         })
//         .catch(error => {
//             console.error('Error fetching districts:', error);
//         });
// }

$(document).ready(function(){
    odoo.define('custom_website.province_selector', function(require){
        var ajax = require('web.ajax');
        ajax.jsonRpc('/get_provinces', 'call', {}).then(function(data){
            var select_sender = $('#province_sender');
            var select_reciever = $('#province_receiver');
            $.each(data, function(index, item){
                select_sender.append(
                    $('<option>', {value: item.id, text: item.name})
                );
                select_reciever.append(
                    $('<option>', {value: item.id, text: item.name})
                );
            });
        });
        $('#province_sender').on('change', function(){
            var province_name = $(this).val();
            var citySelect = $('#district_sender');
            citySelect.empty().append('<option value="">Select city/district</option>');
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
        $('#province_receiver').on('change', function(){
            var province_name = $(this).val();
            var citySelect = $('#district_receiver');
            citySelect.empty().append('<option value="">Select city/district</option>');
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
