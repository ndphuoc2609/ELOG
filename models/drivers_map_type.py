from odoo import fields, models

class View(models.Model):
    """
        Extends the base 'ir.ui.view' model to include a new type of view
        called 'drivers'.
    """
    _inherit = 'ir.ui.view'
    type = fields.Selection(selection_add=[('drivers', "Drivers Map")])

class IrActionsActWindowView(models.Model):
    """
       Extends the base 'ir.actions.act_window.view' model to include
       a new view mode called 'drivers'.
   """
    _inherit = 'ir.actions.act_window.view'
    view_mode = fields.Selection(selection_add=[('drivers', "Drivers Map")],
                                 ondelete={'drivers': 'cascade'})