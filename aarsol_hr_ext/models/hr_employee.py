from odoo import fields, models, api, _
from odoo.exceptions import ValidationError,UserError
import time
from datetime import date , datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT
import logging
import math
import re
_logger = logging.getLogger(__name__)
import pdb


def parse_date(td):
    resYear = float(td.days)/365.0
    resMonth = (resYear - int(resYear))*365.0/30.0
    resDays = int((resMonth - int(resMonth))*30)
    resYear = int(resYear)
    resMonth = int(resMonth)
    return (resYear and (str(resYear) + "Y ") or "") + (resMonth and (str(resMonth) + "M ") or "") + (resMonth and (str(resDays) + "D") or "")


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    code =fields.Char('Code')
    cnic = fields.Char('CNIC', size=15, track_visibility='onchange')

    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    city = fields.Char('City')
    zip = fields.Char('Zip',change_default=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                                   domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    religion = fields.Char('Religion')
    #age = fields.Char("Age", compute='_compute_age')
    age = fields.Char("Age")
    
    joining_date = fields.Date('Joining Date')
    bank_account_title = fields.Char('Account Title')
    bank_account_no = fields.Char('Account No')
    bank_id = fields.Many2one('res.bank','Bank')

    section_id = fields.Many2one('hr.section', 'Section')
    category_id = fields.Many2one('hr.category', 'Category')
    
    payscale_id = fields.Many2one('hr.payscale', 'Payscale', track_visibility='onchange')
    
    publications = fields.Integer('No of Publication', track_visibility='onchange')
    rate_per_publication = fields.Float('Rate Per Publication', track_visibility='onchange')
    increment_date = fields.Date('Increment Date', track_visibility='onchange')

    stage = fields.Integer('Stage')
    leaving_date = fields.Date('Date Of Leaving')
    retirement_date = fields.Date('Retirement Date')
    retired = fields.Boolean('Retired',default=False)
    rebateCateg = fields.Boolean('Rebate Categ')
    appointment_mode_id = fields.Char('Appointment Mode')
    pension_bit = fields.Char('Pension Bit')
    to_be = fields.Boolean('To Be', default=False)

    medical_ids = fields.One2many('hr.employee.medical', 'employee_id', 'Medical History')
    operation_area_id = fields.Many2one('hr.employee.operation.area', string='Operation Area')
    family_ids = fields.One2many('hr.employee.family', 'employee_id', 'Family')
    academic_ids = fields.One2many('hr.employee.academic', 'employee_id', 'Academics')
    experience_ids = fields.One2many('hr.experience', 'employee_id', 'Experience information')

    manual_slips = fields.Integer()
    manual_gross = fields.Float()
    manual_tax = fields.Float()
    rem_slips = fields.Integer()

    gross_salary = fields.Float(compute='get_salary_comp',store=True)
    tax_deducted = fields.Float(compute='get_salary_comp',store=True)
    future_salary = fields.Float(compute='get_salary_comp',store=True)

    @api.depends('birthday')
    def _compute_age(self):
        for rec in self:
            if rec.birthday:
                start = datetime.strptime(str(rec.birthday), OE_DFORMAT)
                end = datetime.strptime(str(time.strftime(OE_DFORMAT)), OE_DFORMAT)
                delta = end - start
                rec.age = parse_date(delta)
                
    @api.constrains('cnic')
    def _check_cnic(self):
        for rec in self:
            if rec.cnic:
                cnic_com = re.compile('^[0-9+]{5}-[0-9+]{7}-[0-9]{1}$')
                a = cnic_com.search(rec.cnic)
                if a:
                    return True
                else:
                    raise UserError(_("CNIC Format is Incorrect. Format Should like this 00000-0000000-0"))
            
    @api.model
    def employee_contract_generation(self, nlimit=10):
        recs = self.env['hr.employee'].search([('to_be','=',True)], limit=nlimit)
        for rec in recs:
            allowances = False
            deductions = False
            contract_vals = ({
                'name' : rec.name + " Contract -1",
                'employee_id' : rec.id,
                'department_id' : rec.department_id and rec.department_id.id or False,
                'state' : 'draft',
                'company_id': 1,
                'type_id' : 1,
                'struct_id' : 1,
                'date_start' : '2019-01-01',
                'wage' : 0.0,
            })
            contract_id = self.env['hr.contract'].create(contract_vals)
            allowances = self.env['allowances.fixation'].search([('code','=',rec.code),('to_be','=',True)])
            deductions = self.env['deductions.fixation'].search([('code', '=', rec.code), ('to_be', '=', True)])

            #Allowances
            if allowances:
                for allowance in allowances:
                    if allowance.head_name_detail == 'Basic Pay':
                        contract_id.wage = allowance.allowance_amount
                        allowance.to_be = False
                    else:
                        salary_allowance = False
                        type_id = allowance.percentage_type_id + 11
                        salary_allowance = self.env['hr.salary.allowances'].search([('name','=',allowance.head_name_detail),('percentage','=',allowance.head_by_percentage),('percentage_type_id','=',type_id)])
                        if salary_allowance:
                            salary_allowance = salary_allowance[0]
                            allow_vals = ({
                                'contract_id' : contract_id.id,
                                'employee_id' : rec.id,
                                'allowance_id' : salary_allowance.id,
                                'amount' : allowance.allowance_amount,
                            })
                            new_allow_rec = self.env['hr.emp.salary.allowances'].create(allow_vals)
                            new_allow_rec.to_be = False

            #Deductions
            if deductions:
                for deduction in deductions:
                    salary_deduction = False
                    type_id = deduction.percentage_type_id + 11
                    salary_deduction = self.env['hr.salary.deductions'].search(
                        [('name', '=', deduction.head_name_detail),('percentage','=',deduction.head_by_percentage),('percentage_type_id','=',type_id)])
                    if salary_deduction:
                        salary_deduction = salary_deduction[0]
                        deduct_vals = ({
                            'contract_id': contract_id.id,
                            'employee_id': rec.id,
                            'allowance_id': salary_deduction.id,
                            'amount': deduction.allowance_amount,
                        })
                        new_deduct_rec = self.env['hr.emp.salary.deductions'].create(deduct_vals)
                        new_deduct_rec.to_be = False

            if contract_id:
                rec.to_be = False
                _logger.info('.......Contract for the Employee %r generated . ..............',
                             contract_id.employee_id.name)

    @api.depends('slip_ids','contract_ids','contract_ids.date_start')
    def get_salary_comp(self):
        for emp in self:
            gross = emp.manual_gross
            tax = emp.manual_tax

            config_fy_start = self.env['ir.config_parameter'].sudo().get_param('aarsol_hr.fiscal_year_start')
            slips = emp.slip_ids.filtered(lambda l: l.state == 'done' and l.date_from >= config_fy_start)
            for slip in slips:
                gross_line = slip.line_ids.filtered(lambda l: l.salary_rule_id.code == 'GROSS')
                if gross_line:
                    gross += gross_line.total
                tax_line = slip.line_ids.filtered(lambda l: l.salary_rule_id.code == 'IT')
                if tax_line:
                    tax += abs(tax_line.total)

            emp.gross_salary = gross
            emp.tax_deducted = tax
            
            if emp.contract_ids:
                config_fy_end = self.env['ir.config_parameter'].sudo().get_param('aarsol_hr.fiscal_year_end')
                fy_end = datetime.strptime(config_fy_end, '%Y-%m-%d')
                # last_date = datetime.strptime('2020-06-30', '%Y-%m-%d').date()
                contract_date = fields.Date.from_string(emp.contract_ids[0].date_start)
                months = min(round(((fy_end - contract_date).days)/30),12)
                # months = 12
                rem_slips = months - len(slips) - emp.manual_slips
                future_salary = (rem_slips -1) * emp.contract_ids[0].wage
                emp.future_salary = future_salary
                emp.rem_slips = rem_slips


class HRContract(models.Model):
    _inherit='hr.contract'

    allowances_ids = fields.One2many('hr.emp.salary.allowances','contract_id', 'Allowances')
    deductions_ids = fields.One2many('hr.emp.salary.deductions', 'contract_id', 'Deductions')


class AllowancesFixation(models.Model):
    _name = 'allowances.fixation'
    _description = 'Allowances Fixations'

    code = fields.Char('Code')
    head_name_detail = fields.Char('Head Name Detail')
    head_id_detail = fields.Char('Head ID Detail')
    head_by_percentage = fields.Float('Head By Percentage')
    percentage_type_id = fields.Integer('Percentage Type')
    allowance_amount = fields.Float('Allowance Amount')
    to_be = fields.Boolean('To Be', default=False)


class DeductionsFixation(models.Model):
    _name = 'deductions.fixation'
    _description = 'Deductions Fixations'

    code = fields.Char('Code')
    head_name_detail = fields.Char('Head Name Detail')
    allowance_amount = fields.Float('Allowance Amount')
    head_id_detail = fields.Char('Head ID Detail')
    head_by_percentage = fields.Float('Head By Percentage')
    percentage_type_id = fields.Integer('Percentage Type')
    to_be = fields.Boolean('To Be', default=False)


class hr_department(models.Model):
    _inherit = "hr.department"
    
    @api.depends('code', 'name')
    def _get_dept_name(self):
        for rec in self:
            rec.short_name = (rec.code or '') + ":" + rec.name
    
    name = fields.Char('Department Name', required=True, translate=True)
    code = fields.Char("Code", size=4)
    abbrev = fields.Char("Abbrev", size=2)
    short_name = fields.Char('Short Name', compute='_get_dept_name', store=True)
    user_ids = fields.Many2many('res.users', 'department_user_rel', 'dept_id', 'user_id', 'Users')


class res_users(models.Model):
    _inherit = 'res.users'
    
    dept_ids = fields.Many2many('hr.department', 'department_user_rel', 'user_id', 'dept_id', 'Departments')
    
    def name_get(self):
        result = []
        for record in self:
            name = "%s - %s" % (record.login, record.name)
            result.append((record.id, name))
        return result
