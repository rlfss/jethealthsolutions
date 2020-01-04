from odoo import api, fields, models, _


class Job(models.Model):
    _inherit = "hr.job"

    alias_id = fields.Many2one('mail.alias', "Alias", required=False)