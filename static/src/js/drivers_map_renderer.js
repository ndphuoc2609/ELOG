/** @odoo-module */
import { useService } from '@web/core/utils/hooks';
import { Component, onMounted, onRendered } from "@odoo/owl";

export class DriversMapRenderer extends Component {
    async setup() {
        this.orm = useService('orm');
        this.action = useService("action");
        this.selectedDriver = false;

        onMounted(() => {
            this.initMap();
        });

        onRendered(() => {
            this.updateMap();
        });
    }

    async initMap() {
        this.transports = await this.orm.searchRead(
            'shipping.order.transport', [],
            ['shipping_order_id', 'type', 'state', 'shift_end', 'from_address', 'from_latitude', 'from_longitude', 'to_address', 'to_latitude', 'to_longitude'],
        );
        this.warehouses = await this.orm.searchRead(
            'stock.warehouse', [],
            ['latitude', 'longitude', 'address'],
        );
        this.zones = await this.orm.searchRead(
            'shipping.zone', [],
            ['latitude', 'longitude', 'radius', 'role_id'],
        );
        this.allDrivers = new Map();
        this.map = L.map('map', { zoomControl: false }).setView(['10.808082292265102', '106.66129906625243'], 7);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "&copy; OpenStreetMap contributors",
        }).addTo(this.map);

        this.props.records.forEach(async (driver) => {
            const driverDetail = this.createDriverDetail(driver);
            this.allDrivers.set(driver.phone, driverDetail);
        });
    }

    async updateMap() {
        this.transports = await this.orm.searchRead(
            'shipping.order.transport', [],
            ['shipping_order_id', 'type', 'state', 'shift_end', 'from_address', 'from_latitude', 'from_longitude', 'to_address', 'to_latitude', 'to_longitude'],
        );
        this.warehouses = await this.orm.searchRead(
            'stock.warehouse', [],
            ['latitude', 'longitude', 'address'],
        );
        this.zones = await this.orm.searchRead(
            'shipping.zone', [],
            ['latitude', 'longitude', 'radius', 'role_id'],
        );
        if (this.map) {
            var currentCenter = this.map.getCenter();
            var visibleDrivers = [];
            this.props.records.forEach(async (driver) => {
                visibleDrivers.push(driver.phone);
                if (this.allDrivers.has(driver.phone)) {
                    this.allDrivers.get(driver.phone).get('marker').setLatLng([driver.driver_latitude, driver.driver_longitude]);
                } else {
                    const driverDetail = this.createDriverDetail(driver);
                    this.allDrivers.set(driver.phone, driverDetail);
                }
            });
            this.allDrivers.forEach((driver, driverPhone) => {
                const marker = driver.get("marker");
                if (visibleDrivers.includes(driverPhone)) {
                    if (!this.map.hasLayer(marker)) {
                        this.map.addLayer(marker);
                    }
                } else {
                    this.map.removeLayer(marker);
                }
            });
            this.map.setView(currentCenter);
        }
    }

    createDriverDetail(driver) {
        var driverDetail = new Map();
        var driverInfo = driver.name + "<br/>" + driver.phone + "<br/>";
        if (driver.driver_is_online) {
            driverInfo += "Online";
        } else {
            driverInfo += "Offline";
        }
        driverInfo = "<p>" + driverInfo + "</p>";
        var driverMarker = L.marker([driver.driver_latitude, driver.driver_longitude]).addTo(this.map).bindPopup(driverInfo);

        var transportMarkers = [];
        if (driver.driver_transports.length > 0) {
            const transports = this.transports.filter(transport => driver.driver_transports.includes(transport.id));

            transports.forEach(transport => {
                var icon = undefined;
                var lat = undefined;
                var lng = undefined;
                var address = undefined;
                if (transport.state == 'new') {
                    icon = '<i style="color:blue" class="fa fa-motorcycle fa-2x"></i>';
                }
                else if (transport.state == 'in_progress') {
                    icon = '<i style="color:orange" class="fa fa-circle fa-2x"></i><span style="color:white; margin-left:-15px"></span>';
                }
                else if (transport.state == 'completed') {
                    icon = '<i style="color:green" class="fa fa-motorcycle fa-2x"></i>';
                }
                else if (transport.state == 'failed') {
                    icon = '<i style="color:red" class="fa fa-motorcycle fa-2x"></i>';
                }
                if (transport.type == 'pickup') {
                    lat = transport.from_latitude;
                    lng = transport.from_longitude;
                    address = transport.from_address;
                }
                else if (transport.type == 'delivery') {
                    if (transport.state != 'in_progress') {
                        icon = icon.slice(0, -6) + ' fa-flip-horizontal"></i>';
                    }
                    lat = transport.to_latitude;
                    lng = transport.to_longitude;
                    address = transport.to_address;
                }
                
                icon = L.divIcon({
                    html: icon,
                    iconSize: [20, 20],
                    popupAnchor: [0, -21],
                    className: 'fa-layers fa-fw'
                });
                var markerInfo = '<p><a id="order" href="#" data="' + transport.shipping_order_id[0] + '">' + transport.shipping_order_id[1] + '</a><br/>' + address + '</p>';
                var marker = L.marker([lat, lng], { icon: icon }).bindPopup(markerInfo);
                marker.on('click', () => {                    
                    var orderLink = document.getElementById("order");
                    if (orderLink) {
                        orderLink.addEventListener("click", (e) => {
                            e.preventDefault();
                            var data = orderLink.getAttribute("data");
                            this.openOrder(data);
                            return false;
                        });
                    }
                });
                transportMarkers.push(marker);
            });
        }

        var warehouses = this.warehouses.filter(warehouse => warehouse.id == driver.warehouse_id[0]);
        var warehouse = warehouses[0];

        var warehouseInfo = driver.warehouse_id[1] + "<br/>" + warehouse.address + "<br/>";
        warehouseInfo = "<p>" + warehouseInfo + "</p>";
        var warehouseMarker = L.marker([warehouse.latitude, warehouse.longitude], { 
            icon: L.divIcon({
                html: '<i class="fa fa-cubes fa-2x"></i>',
                iconSize: [20, 20],
                className: 'fa-layers fa-fw'
            }) 
        }).bindPopup(warehouseInfo);

        var workingZone = this.zones.filter(zone => zone.role_id[0] == driver.default_planning_role_id[0]);
        if (workingZone.length > 0) {
            var workingZone = workingZone[0];
            var circleOptions = {
                fillColor: 'blue',
                fillOpacity: 0.2,
                radius: workingZone.radius * 1000,
            };
            var workingCircle = L.circle([workingZone.latitude, workingZone.longitude], circleOptions);
            driverDetail.set("workingCircle", workingCircle);
        }

        driverMarker.on('click', () => {
            this.toggleShowRelatedMarkers(driver.phone);
        });
        driverDetail.set("info", driver);
        driverDetail.set("marker", driverMarker);
        driverDetail.set("transportMarkers", transportMarkers);
        driverDetail.set("warehouseMarker", warehouseMarker);
        return driverDetail;
    }

    toggleShowRelatedMarkers(driverPhone) {
        if (this.selectedDriver) {
            // remove all markers
            const transportMarkers = this.allDrivers.get(this.selectedDriver).get('transportMarkers');
            transportMarkers.forEach(marker => {
                if (this.map.hasLayer(marker)) {
                    this.map.removeLayer(marker);
                }
            });
            const warehouseMarker = this.allDrivers.get(this.selectedDriver).get('warehouseMarker');
            if (this.map.hasLayer(warehouseMarker)) {
                this.map.removeLayer(warehouseMarker);
            }
            const workingCircle = this.allDrivers.get(this.selectedDriver).get('workingCircle');
            if (workingCircle && this.map.hasLayer(workingCircle)) {
                this.map.removeLayer(workingCircle);
            }
        }
        if (driverPhone != this.selectedDriver) {
            const transportMarkers = this.allDrivers.get(driverPhone).get('transportMarkers');
            transportMarkers.forEach(marker => {
                this.map.addLayer(marker);
            });
            const warehouseMarker = this.allDrivers.get(driverPhone).get('warehouseMarker');
            this.map.addLayer(warehouseMarker);
            const workingCircle = this.allDrivers.get(driverPhone).get('workingCircle');
            if (workingCircle) {
                this.map.addLayer(workingCircle);
            }
            this.selectedDriver = driverPhone;
        } else {
            this.selectedDriver = false;
        }
    }

    openOrder(orderId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'shipping.order',
            res_id: parseInt(orderId),
            views: [[false, 'form']],
            target: 'current',
        });
    }
}

DriversMapRenderer.template = "custom_website.Renderer";