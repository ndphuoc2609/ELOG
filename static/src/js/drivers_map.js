/** @odoo-module */

import { registry } from "@web/core/registry";
import { DriversMapController } from "./drivers_map_controller";
import { DriversMapArchParser } from "./drivers_map_arch_parser";
import { DriversMapModel } from "./drivers_map_model";
import { DriversMapRenderer } from "./drivers_map_renderer";

export const driversMapView = {
    type: "drivers",
    display_name: "Map",
    icon: "fa fa-map",
    multiRecord: true,
    Controller: DriversMapController,
    ArchParser: DriversMapArchParser,
    Model: DriversMapModel,
    Renderer: DriversMapRenderer,

    props(genericProps, view) {
        const { ArchParser } = view;
        const { arch } = genericProps;
        const archInfo = new ArchParser().parse(arch);

        return {
            ...genericProps,
            Model: view.Model,
            Renderer: view.Renderer,
            archInfo,
        };
    },
};

registry.category("views").add("drivers", driversMapView);