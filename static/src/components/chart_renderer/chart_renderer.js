/** @odoo-module */

import { registry } from "@web/core/registry"
import { loadJS } from "@web/core/assets"
const { Component, onWillStart, useRef, onMounted, onWillUnmount, onWillUpdateProps } = owl

export class ChartRenderer extends Component {
    setup(){
        this.chartRef = useRef("chart");
        this.chartInstance = null;
        onWillStart(async ()=>{
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js")
        });

        onMounted(()=>this.renderChart());
        onWillUpdateProps(()=>this.renderChart());
        onWillUnmount(()=>{
            if (this.chartInstance){
                this.chartInstance.destroy();
                this.chartInstance = null;
            }
        })
    }

    renderChart(){

        if (this.chartInstance){
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
        
        const chartData = this.props.chartData;
        if (!chartData) return;
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
        this.chartInstance = new Chart(this.chartRef.el, {
            type: this.props.type || 'pie',
            data: chartData,
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: this.props.title, position: 'bottom' }
                }
            },
        });
    }
}

ChartRenderer.template = "owl.ChartRenderer"