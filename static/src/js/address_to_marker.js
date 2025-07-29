document.addEventListener('DOMContentLoaded', function() {
    let debounceTimer;
    let currentMarker = null; 
    let isInputFocused = false;

    const toAddressInput = document.getElementById('to_address');
    const toProvinceReceiver = document.getElementById('province_receiver');
    const toDistrictReceiver = document.getElementById('district_receiver');
    
    toAddressInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const address_value = this.value;
        const nameProvince = toProvinceReceiver.options[toProvinceReceiver.selectedIndex].text;
        const nameDistrict = toDistrictReceiver.options[toDistrictReceiver.selectedIndex].text;
        const address = address_value + ' ' + nameDistrict + ' ' + nameProvince;

        debounceTimer = setTimeout(() => {
            if (address) {
                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.length > 0) {
                            const { lat, lon } = data[0];
                            map.setView([lat, lon], 17);
                            addToMarker(lat, lon, 'To: ' + address);
                            document.getElementById('to_latitude').value = lat;
                            document.getElementById('to_longitude').value = lon; 
                        }
                    })
                    .catch(error => console.error('Error:', error));
            }
        }, 500);
    });

    document.getElementById("to_address").addEventListener("focus",function(e){
        const provinceValue = toProvinceReceiver.value;
        const districtValue = toDistrictReceiver.value;
    
        if (provinceValue !== "" && districtValue !== "") {
            isInputFocused = true;
            toProvinceReceiver.style.borderColor = 'black';
            toDistrictReceiver.style.borderColor = 'black';
        } else {
            isInputFocused = false;
            toProvinceReceiver.style.borderColor = 'red';
            toDistrictReceiver.style.borderColor = 'red';
        }
    });

    map.on('click', function(e) {
        if (isInputFocused) {
            const { lat, lng } = e.latlng;
            addToMarker(lat, lng, 'To');

            document.getElementById('to_latitude').value = lat;
            document.getElementById('to_longitude').value = lng;
            isInputFocused = false;
            map.setView([lat, lng], 17);

            fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&accept-language=vi`)
                .then(response => response.json())
                .then(data => {
                    if (data.display_name) {
                        toAddressInput.value = data.display_name.replace(/,\s*\d{5},\s*Việt Nam$/, '');
                    }
                })
                .catch(error => console.error('Error:', error));
        }
    });

    function addToMarker(lat, lon, popupText) {
        if (currentMarker) {
            map.removeLayer(currentMarker);
        }

        currentMarker = L.marker([lat, lon]).addTo(map)
            .bindPopup(popupText)
            .openPopup();
    };
});