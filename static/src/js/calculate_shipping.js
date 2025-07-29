document.addEventListener('DOMContentLoaded', function() {
    // Các biến toàn cục
    let currentMarker = null; 

    const fromLatInput = document.getElementById('from_latitude');
    const fromLonInput = document.getElementById('from_longitude');
    const toLatInput = document.getElementById('to_latitude');
    const toLonInput = document.getElementById('to_longitude');

    function updateShippingFee() {
        const fromLat = parseFloat(fromLatInput.value);
        const fromLon = parseFloat(fromLonInput.value);
        const toLat = parseFloat(toLatInput.value);
        const toLon = parseFloat(toLonInput.value);

        if (!isNaN(fromLat) && !isNaN(fromLon) && !isNaN(toLat) && !isNaN(toLon)) {
            const fromPoint = L.latLng(fromLat, fromLon);
            const toPoint = L.latLng(toLat, toLon);
            const distance = fromPoint.distanceTo(toPoint) / 1000; 

            const shippingFee = distance * 10000; 
            const formattedFee = formatShippingFee(shippingFee);
            document.getElementById('shipping_fee_display').textContent = formattedFee + ' VNĐ';
        } else {
            document.getElementById('shipping_fee_display').textContent = '20,000 VNĐ';
        }
    }

    function formatShippingFee(shippingFee) {
        const roundedFee = Math.ceil(shippingFee * 10) / 10;
        const parts = roundedFee.toString().split('.');
        const integerPart = parts[0];
        const decimalPart = parts.length > 1 ? '.' + parts[1] : '';
    
        const formattedIntegerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    
        return formattedIntegerPart;
    }

    map.on('click', function(e) {
        updateShippingFee();
    });
});