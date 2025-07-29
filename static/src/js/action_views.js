function addRow() {
    var productName = $('input[name="product_name_0"]').val();
    var weight = $('input[name="weight_0"]').val();
    var dimensions = $('input[name="dimensions_0"]').val();
    var shipmentValue = $('input[name="shipment_value_0"]').val();

    if (!productName) {
        alert("Please enter a description for the package.");
        return;
    }
    if (!weight) {
        alert("Please provide the weight of the package.");
        return;
    }
    if (!dimensions) {
        alert("Please enter the dimensions of the package (length, width, height).");
        return;
    }
    else {
        const regex = /^\d+x\d+x\d+$/;
        if (!regex.test(dimensions)) {
            alert("Dimensions must have format LxWxH");
            return;
        }
    }
    if (!shipmentValue) {
        alert("Please provide the value of the package.");
        return;
    }

    var rowCount = $('#product_body tr').length + 1;

    var newRow = '<tr>' +
        '<td>' + productName + '</td>' +
        '<td>' + weight + '</td>' +
        '<td>' + dimensions + '</td>' +
        '<td>' + parseInt(shipmentValue, 10).toLocaleString('en-US') + ' VND</td>' +
        '<td class="action-icon">' +
        '<i class="fas fa-pen" onclick="editRow(this)"></i>' +
        '<i class="fas fa-times" onclick="deleteRow(this)"></i>' +
        '</td>' +
        '</tr>';

    $('#product_body').append(newRow);

    updateTotals();

    // Clear the input fields after adding the row
    $('input[name="product_name_0"]').val('');
    $('input[name="weight_0"]').val('');
    $('input[name="dimensions_0"]').val('');
    $('input[name="shipment_value_0"]').val('');
}

function editRow(icon) {
    var row = $(icon).closest('tr');
    var cells = row.find('td');
    cells.each(function () {
        var cell = $(this);
        if (cell.index() >= 0 && cell.index() < 4) {
            var input = $('<input>', {
                type: 'text',
                value: cell.text(),
                class: 'form-control'
            });
            cell.html(input);
        }
    });
    $(icon).removeClass('fa-pen').addClass('fa-save').attr('onclick', 'saveRow(this)');
}

function saveRow(icon) {
    var row = $(icon).closest('tr');
    var cells = row.find('td');
    cells.each(function () {
        var cell = $(this);
        if (cell.index() >= 0 && cell.index() < 4) {
            var input = cell.find('input');
            cell.html(input.val());
        }
    });
    $(icon).removeClass('fa-save').addClass('fa-pen').attr('onclick', 'editRow(this)');
    updateTotals();
}

function deleteRow(icon) {
    $(icon).closest('tr').remove();
    updateTotals();
}

function updateTotals() {
    var totalWeight = 0;
    var totalShipmentValue = 0;
    var totalDimensions = 0;

    $('#product_body tr').each(function (index) {
        if (index > 0) {
            var weight = parseFloat($(this).find('td').eq(1).text());
            const [length, width, height] = $(this).find('td').eq(2).text().split('x').map(Number);
            var dimensions = length * width * height;
            var shipmentValueText = $(this).find('td').eq(3).text();
            var shipmentValue = parseInt(shipmentValueText.replace(/[^\d]/g, ''));
    
            totalWeight += weight;
            totalShipmentValue += shipmentValue;
            totalDimensions += dimensions / 6000;
        }
    });

    $('#total_weight').text(totalWeight.toLocaleString('de-DE') + ' kg');
    $('#total_dimensions').text(totalDimensions);
    $('#total_shipment_value').text(totalShipmentValue.toLocaleString('en-US') + ' VND');
    updateShippingFee();
}

function getRegion(index) {
    if (index < 26) {
        return 0; // Bắc
    }
    else if (index < 45) {
        return 1; // Trung
    }
    else {
        return 2; // Nam
    }
}

function updateShippingFee() {
    var senderProvinceIdx = $('#province_sender').prop('selectedIndex');
    var receiverProvinceIdx = $('#province_receiver').prop('selectedIndex');
    if (senderProvinceIdx == 0 || receiverProvinceIdx == 0){
        return;
    }
    var senderRegion = getRegion(senderProvinceIdx);
    var receiverRegion = getRegion(receiverProvinceIdx);
    console.log(senderProvinceIdx);
    console.log(receiverProvinceIdx);
    var type = -1;
    if ((senderProvinceIdx == 1 && receiverProvinceIdx == 50) || (senderProvinceIdx == 50 && receiverProvinceIdx == 1)) { // Special case
        type = 1;
    }
    else if (senderProvinceIdx == receiverProvinceIdx) { // Same province
        type = 0;
    }
    else if (senderRegion == receiverRegion) { // Same region
        type = 1;
    }
    else { // Inter region
        type = 2;
    }
    var totalWeight = parseInt($('#total_weight').text().replace(' kg', '').replaceAll('.', ''));
    var totalDimensions = parseInt($('#total_dimensions').text());
    var maxTotal = Math.ceil(Math.max(totalWeight, totalDimensions));
    var shippingFee = 0;
    if (maxTotal <= 1) {
        shippingFee = 20000 + type * 5000;
    }
    else if (maxTotal <= 3) {
        shippingFee = 25000 + type * 5000;
    }
    else if (maxTotal <= 5) {
        shippingFee = 30000 + type * 5000;
    }
    else {
        shippingFee = 30000 + type * 5000 + (maxTotal - 5) * (3000 + 2000 * type);
    }
    $('#shipping_fee_display').text(shippingFee.toLocaleString('en-US') + ' VND');
}

$(document).ready(function () {
    $('#province_sender').on('change', function(){
        updateShippingFee();
    });

    $('#province_receiver').on('change', function(){
        updateShippingFee();
    });

    $('form').on('submit', function () {
        // Check if there is at least one product row (not counting the input row)
        const rows_body = $('#product_body tr');
        if (rows_body.length <= 1) {
            alert('Please add at least one package to proceed.');
            $('.btnsubmit').prop('disabled', false).text('Order Now');
            return false;
        }

        const receiver_phone = $('#receiver_phone').val();
        const phoneRegex = /^0\d{9}$/;
        if (!phoneRegex.test(receiver_phone)) {
            alert('Invalid Phone number!');
            $('.btnsubmit').prop('disabled', false).text('Order Now');
            return false;
        }

        //lock button submit
        var $btn = $('.btnsubmit');
        $btn.prop('disabled', true).text('Processing...');

        // Get the first row's input elements to determine column names
        const colNames = [];
        $('table tr:first-child td input').each(function() {
          colNames.push($(this).attr('name').slice(0, -2));
        });
        
        // update total to form 
        var shippingFeeText = $('#shipping_fee_display').text();
        var shippingFee = shippingFeeText.match(/\d+/g).join('');
        shippingFee = parseInt(shippingFee, 10);
        $('#shipping_fee_input').val(shippingFee);

        if ($('#insurance_fee').is(':visible')) {
            var insuranceFeeText = $('#insurance_fee').text().replaceAll(',', '');
            var insuranceFee = insuranceFeeText.match(/\d+/)
            insuranceFeeValue = parseInt(insuranceFee[0], 10); 
            $('#insurance_fee_input').val(insuranceFeeValue);
        }

        if ($('#promotion_discount').is(':visible')) {
            const promotion_discount_val = $('#promotion_discount').text().trim().replace(' VND', '').replaceAll('.', '').replaceAll(',', '');
            const promotionDiscountValue = parseInt(promotion_discount_val, 10); 
            $('#promotion_discount_input').val(promotionDiscountValue);
        }
        const total_fee = $('#total_fee').text().trim().replace(' VND', '').replaceAll('.', '').replaceAll(',', '');
        $('#total_fee_input').val(total_fee);

        // Get the table rows
        const rows = $('#product_body tr');
 
        // Loop through each row and create hidden input fields for text content
        rows.each(function (rowIndex) {
            const cells = $(this).find('td');
            cells.each(function (cellIndex) {
                if (cellIndex >= 0 && cellIndex < 4) {
                    const textContent = $(this).text().trim();
                    if (textContent) {
                        // Create a hidden input field
                        const hiddenInput = $('<input>').attr({
                            type: 'hidden',
                            name: `${colNames[cellIndex]}_${rowIndex}`,
                            value: textContent
                        });
 
                        // Append the hidden input field to the form
                        $('form').append(hiddenInput);
                    }
                }
            });
        });
    });
});