/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted } from "@odoo/owl";

class LeafletMap extends Component {
    setup() {
        this.orm = useService("orm");
        this.record = this.props.record;

        onMounted(() => {
            this.initMap();
        });
    }

    initMap() {
        if (!this.map) {
            var from_lat = this.record.data.from_latitude || '10.808082292265102';
            var from_lng = this.record.data.from_longitude || '106.66129906625243';
            var to_lat = this.record.data.to_latitude || '10.799991371322742';
            var fo_lng = this.record.data.to_longitude || '106.66068094290497';
            this.map = L.map('map').setView([from_lat, from_lng], 13);

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "&copy; OpenStreetMap contributors",
            }).addTo(this.map);

            const startMarker = L.marker([from_lat, from_lng], { draggable: true, autoPan: true,
                icon: L.icon({
                  iconUrl: 'https://img.icons8.com/?size=100&id=20390&format=png&color=000000',
                  iconSize: [25, 25], // Size of the icon
                  iconAnchor: [12, 12], // Anchor point of the icon
                  popupAnchor: [1, 1], // Anchor point of the popup
                })
              }).bindPopup('Start Point').addTo(this.map);
        
              const endMarker = L.marker([to_lat, fo_lng], {
                icon: L.icon({
                  iconUrl: 'https://img.icons8.com/?size=100&id=86315&format=png&color=000000',
                  iconSize: [25, 25], // Size of the icon
                  iconAnchor: [12, 12], // Anchor point of the icon
                  popupAnchor: [1, 1], // Anchor point of the popup
                })
              }).bindPopup('End Point').addTo(this.map);

            startMarker.on('drag', async (event) => {
                var marker = event.target;
                var position = marker.getLatLng();
                from_lat = position.lat;
                from_lng = position.lng;
                
                // Save the updated coordinates to the server
                await this.orm.write(this.record.resModel, [this.record.resId], {
                    from_latitude: position.lat,
                    from_longitude: position.lng,
                });
            });

            if (window.routingControl) {
                this.map.removeControl(window.routingControl);
            }
            if (window.routingControl) {
                this.map.removeControl(window.routingControl);
              }
            window.routingControl = L.Routing.control({
                waypoints: [
                    L.latLng(from_lat, from_lng),
                    L.latLng(to_lat, fo_lng)
                ],
                routeWhileDragging: true,
                show: false,
                createMarker: function(i, waypoint, n) {
                    // Use the custom markers created above
                    if (i === 0) {
                        return startMarker;
                    } else if (i === 1) {
                        return endMarker;
                    }
                }
            }).addTo(this.map);
        }
    }
}

LeafletMap.template = "custom_website.LeafletMapWidget";
registry.category("view_widgets").add("leaflet_map", LeafletMap);
