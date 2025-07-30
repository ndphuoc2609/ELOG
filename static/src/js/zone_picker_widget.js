/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onRendered, useRef } from "@odoo/owl";
import { useInputField } from "@web/views/fields/input_field_hook";

class ZonePickerWidget extends Component {
    static template = "custom_website.ZonePickerWidget";
    setup() {
        this.orm = useService("orm");
        this.input = useRef('inputarea')
        useInputField({ getValue: () => this.props.value || "", refName: "inputarea" });

        onMounted(() => {
            this.initMap();
        });

        onRendered(() => {
            this.updateArea();
        });
    }

    async initMap() {
        if (!this.map) {
            this.zones = await this.orm.searchRead(
                'shipping.zone', [],
                ['area', 'name'],
            );
            this.map = L.map('map').setView(['10.808082292265102', '106.66129906625243'], 7);

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "&copy; OpenStreetMap contributors",
            }).addTo(this.map);

            this.drawnItems = new L.FeatureGroup();
            this.map.addLayer(this.drawnItems);

            var drawControl = new L.Control.Draw({
                edit: {
                    featureGroup: this.drawnItems,
                    remove: false
                },
                draw: {
                    polygon: true,
                    polyline: false,
                    rectangle: false,
                    marker: false,
                    circlemarker: false,
                    circle: false
                }
            });
            this.map.addControl(drawControl);

            this.zones.forEach(zone => {
                var options = {
                    color: 'red',
                    fillColor: 'red',
                    fillOpacity: 0.2,
                };
                if (!this.props.value || zone.area != this.props.value) {
                    area = L.polygon(JSON.parse(zone.area), options).bindPopup(zone.name).addTo(this.map);
                }
            });

            if (this.props.value) {
                var area = L.polygon(JSON.parse(this.props.value));
                this.drawnItems.addLayer(area);
                this.map.fitBounds(area.getBounds());
            }

            function CreateZone(event) {
                // Check if there is already a zone on the map
                this.drawnItems.eachLayer((layer) => {
                    this.drawnItems.removeLayer(layer);
                });

                // If a zone already exists, remove the newly drawn zone
                var newLayer = event.layer;
                if (!newLayer) {
                    event.layers.eachLayer((layer) => {
                        newLayer = layer;
                    });
                }
                // Add the new zone layer to the map
                this.drawnItems.addLayer(newLayer);

                var coordinates = newLayer.getLatLngs()[0];
                var coordList = coordinates.map(function (latlng) {
                    return `[${latlng.lat}, ${latlng.lng}]`;
                });

                var coordString = `[${coordList.join(', ')}]`;
                this.props.update(coordString);
            }

            this.map.on(L.Draw.Event.CREATED, (e) => {CreateZone.call(this, e)});
            this.map.on(L.Draw.Event.EDITED, (e) => {CreateZone.call(this, e)});
        }
    }

    updateArea() {
        if (this.props.value && this.drawnItems) {
            this.drawnItems.eachLayer((layer) => {
                this.drawnItems.removeLayer(layer);
            });
            var area = L.polygon(JSON.parse(this.props.value));
            this.drawnItems.addLayer(area);
        }
    }
}

registry.category("fields").add("zone_picker", ZonePickerWidget);
