/** @odoo-module */

import { registry } from "@web/core/registry"
import { KpiCard } from "./kpi_card/kpi_card"
import { ChartRenderer } from "./chart_renderer/chart_renderer"
import { useState } from "@odoo/owl"
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart } = owl

export class OwlShippingDashboard extends Component {
    setup() {
        this.state = useState({
            period: "1",
            total_shipments: 0,
            total_shipments_percent: 0,
            pickup_progress: 0,
            pickup_progress_percent: 0,
            delivery_progress: 0,
            delivery_progress_percent: 0,
            total_fees: 0,
            total_fees_percent: 0,
            warehouseList: [],
            warehouseSearch: "",
            selectedWarehouse: "",
            showWarehouseDropdown: false,
        });
        this.rpc = useService("rpc");
        onWillStart(async () => {
            await this.loadWarehouses();
            await this.loadData();
        });
    }

    async loadWarehouses() {
        const warehouses = await this.rpc("/custom_website/get_warehouses", {});
        this.state.warehouseList = warehouses;
    }

    get filteredWarehouses() {
        const search = (this.state.warehouseSearch || "").toLowerCase();
        return this.state.warehouseList.filter(
            wh => !search || wh.name.toLowerCase().includes(search)
        );
    }

    onWarehouseSearch(ev) {
        this.state.warehouseSearch = ev.target.value;
        this.state.showWarehouseDropdown = true;
    }

    onWarehouseFocus() {
        this.state.showWarehouseDropdown = true;
    }

    onWarehouseBlur() {
        setTimeout(() => { 
            this.state.showWarehouseDropdown = false;
        }, 150);
    }

    async clearWarehouse() {
        this.state.selectedWarehouse = "";
        this.state.warehouseSearch = "";
        this.state.showWarehouseDropdown = false;
        await this.loadData();
    }

    async selectWarehouse(wh) {
        this.state.selectedWarehouse = wh.id;
        this.state.warehouseSearch = wh.name;
        this.state.showWarehouseDropdown = false;
        await this.loadData();
    }

    async onPeriodChange(ev) {
        this.state.period = ev.target.value;
        await this.loadData();
        await this.loadData();
    }

    async loadData() {
        console.log("Loading shipping dashboard data for period:", this.state.period, "and warehouse:", this.state.selectedWarehouse);
        const data = await this.rpc("/custom_website/shipping_dashboard_stats", {
            period: this.state.period,
            warehouse_name: this.state.warehouseSearch || null,
        });
        
        this.state.total_shipments = data.total_shipments;
        this.state.total_shipments_percent = data.total_shipments_percent;
        this.state.pickup_progress = data.pickup_progress;
        this.state.pickup_progress_percent = data.pickup_progress_percent;
        this.state.delivery_progress = data.delivery_progress;
        this.state.delivery_progress_percent = data.delivery_progress_percent;
        this.state.total_fees = data.total_fees;
        this.state.total_fees_percent = data.total_fees_percent;
        
        this.state.orderStatusChart = data.order_status_chart;
        console.log("Order Status Chart Data:", this.state.orderStatusChart);
    }

}

OwlShippingDashboard.template = "owl.shipping_dashboard";
OwlShippingDashboard.components = { KpiCard, ChartRenderer }

registry.category("actions").add("owl.shipping_dashboard", OwlShippingDashboard)