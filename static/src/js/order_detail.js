
$(document).ready(function () {
    const map = L.map('map');
    const fromLatitude = parseFloat('<t t-esc="order.from_latitude"/>');
    const fromLongitude = parseFloat('<t t-esc="order.from_longitude"/>');
    const toLatitude = parseFloat('<t t-esc="order.to_latitude"/>');
    const toLongitude = parseFloat('<t t-esc="order.to_longitude"/>');

    map.setView([fromLatitude, fromLongitude], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
    }).addTo(map);

    const startMarker = L.marker([fromLatitude, fromLongitude], { draggable: false, autoPan: true,
        icon: L.icon({
        iconUrl: 'https://img.icons8.com/?size=100&amp;id=20390&amp;format=png&amp;color=000000',
        iconSize: [25, 25], 
        iconAnchor: [12, 12], 
        popupAnchor: [1, 1], 
        })
    }).bindPopup('From: <t t-esc="order.from_address"/>').addTo(map);

    const endMarker = L.marker([toLatitude, toLongitude], { draggable: false, autoPan: true,
        icon: L.icon({
        iconUrl: 'https://img.icons8.com/?size=100&amp;id=86315&amp;format=png&amp;color=000000',
        iconSize: [25, 25],
        iconAnchor: [12, 12], 
        popupAnchor: [1, 1],
        })
    }).bindPopup('To: <t t-esc="order.to_address"/>').addTo(map);

    if (window.routingControl) {
        map.removeControl(window.routingControl);
    }
    if (window.routingControl) {
        map.removeControl(window.routingControl);
    }
    window.routingControl = L.Routing.control({
        waypoints: [
            L.latLng(fromLatitude, fromLongitude),
            L.latLng(toLatitude, toLongitude)
        ],
        routeWhileDragging: true,
        show: false,
        createMarker: function(i, waypoint, n) {
            if (i === 0) {
                return startMarker;
            } else if (i === 1) {
                return endMarker;
            }
        }
    }).addTo(map);
});