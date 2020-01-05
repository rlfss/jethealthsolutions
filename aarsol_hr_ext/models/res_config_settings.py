from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fiscal_year_start = fields.Char(string='Start Date', config_parameter='aarsol_hr.fiscal_year_start',default = '2019-07-01')
    fiscal_year_end = fields.Char(string='Last Date', config_parameter='aarsol_hr.fiscal_year_end', default='2019-06-30')