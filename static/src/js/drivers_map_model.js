/** @odoo-module */

import { KeepLast } from "@web/core/utils/concurrency";

export class DriversMapModel {
    constructor(orm, resModel, fields, archInfo, domain) {
        this.orm = orm;
        this.resModel = resModel;
        // We can access arch information parsed by the beautiful arch parser
        const { fieldFromTheArch } = archInfo;
        this.fieldFromTheArch = fieldFromTheArch;
        this.fields = fields;
        this.domain = domain;
        this.keepLast = new KeepLast();
        this.records = [];
        this.recordsLength = 0;
    }

    async load() {
        // The keeplast protect against concurrency call
        const { length, records } = await this.keepLast.add(
            this.orm.webSearchRead(this.resModel, this.domain, ["name", "phone", "warehouse_id", "driver_is_online", "driver_latitude", "driver_longitude", "driver_transports", "default_planning_role_id"], {})
        );
        this.records = records;
        this.recordsLength = length;
        return this.records;
    }
}