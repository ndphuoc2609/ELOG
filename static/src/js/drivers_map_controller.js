/** @odoo-module */

import { Layout } from "@web/search/layout";
import { useService, useBus } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillDestroy, useState} from "@odoo/owl";

export class DriversMapController extends Component {
    setup() {
        this.orm = useService("orm");

        // The controller create the model and make it reactive so whenever this.model is
        // accessed and edited then it'll cause a rerendering
        this.model = useState(
            new this.props.Model(
                this.orm,
                this.props.resModel,
                this.props.fields,
                this.props.archInfo,
                this.props.domain
            )
        );

        onWillStart(async () => {
            await this.model.load();
            this.intervalId = setInterval(() => this.updateRecords(), 10000);
        });

        onWillDestroy(() => {
            clearInterval(this.intervalId);
        });

        if (this.env.searchModel) {
            useBus(this.env.searchModel, "update", async () => {
                const { domain, globalContext } = this.env.searchModel;
                this.model.domain = domain;
                this.updateRecords();
            });
        }
    }

    async updateRecords() {
        this.model.records = await this.model.load();
    }
}

DriversMapController.template = "custom_website.View";
DriversMapController.components = { Layout };