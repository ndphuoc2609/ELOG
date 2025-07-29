document.addEventListener('DOMContentLoaded', function() {
    let debounceTimer;
    let currentMarker = null; 
    let isInputFocused = false;

    const toAddressInput = document.getElementById('from_address');
    const toProvinceSender = document.getElementById('province_sender');
    const toDistrictSender = document.getElementById('district_sender');

    toAddressInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const address_value = this.value;
        const nameProvince = toProvinceSender.options[toProvinceSender.selectedIndex].text;
        const nameDistrict = toDistrictSender.options[toDistrictSender.selectedIndex].text;
        // const address = address_value + ' ' + nameDistrict + ' ' + nameProvince;
        
        const addressParams = {
            street: address_value ? address_value : '',
            city: nameDistrict,
            state: nameProvince,
            country: 'Vietnam'
        };
        
        debounceTimer = setTimeout(() => {
            const query = new URLSearchParams(addressParams).toString();
            if (query) {
                fetch(`https://nominatim.openstreetmap.org/search?${query}&format=json`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.length > 0) {
                            const { lat, lon } = data[0];
                            map.setView([lat, lon], 17);
                            addToMarker(lat, lon, 'From: ' + address);
                            document.getElementById('from_latitude').value = lat;
                            document.getElementById('from_longitude').value = lon; 
                        }
                    })
                    .catch(error => console.error('Error:', error));
            }
        }, 500);
    });

    toAddressInput.addEventListener("focus", function(e) {
        const provinceValue = toProvinceSender.value;
        const districtValue = toDistrictSender.value;
    
        if (provinceValue !== "" && districtValue !== "") {
            isInputFocused = true;
            toProvinceSender.style.borderColor = 'black';
            toDistrictSender.style.borderColor = 'black';
        } else {
            isInputFocused = false;
            toProvinceSender.style.borderColor = 'red';
            toDistrictSender.style.borderColor = 'red';
        }
    });

    map.on('click', function(e) {
        if (isInputFocused) {
            const { lat, lng } = e.latlng;
            addToMarker(lat, lng, 'To');

            document.getElementById('from_latitude').value = lat;
            document.getElementById('from_longitude').value = lng;

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