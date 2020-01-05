from odoo import fields, models, api, _
from odoo.exceptions import ValidationError,UserError
import pdb

import logging
_logger = logging.getLogger(__name__)


class HRSalaryPercentageType(models.Model):
    _name = "hr.salary.percentage.type"
    _description = 'HR Salary Percentage Type'
    
    name = fields.Char('Name')
    code = fields.Char('Code')
    

class HRSalaryRules(models.Model):
    _name = "hr.salary.rules"
    _description = 'HR Salary Rules'
    
    salary_structure_id = fields.Many2one('hr.payroll.structure','Salary Structure')
    account_id = fields.Many2one('account.account','Account')
    allowance_id = fields.Many2one('hr.salary.allowances','Allowance')
    deduction_id = fields.Many2one('hr.salary.deductions', 'Deduction')
    salary_rule_id = fields.Many2one('hr.salary.rule', 'Salary Rule')

    @api.model
    def create(self, vals):
        res = super(HRSalaryRules, self).create(vals)
        if res.allowance_id.code or res.deduction_id.code:
            res.create_salary_rule()
        return res

    def write(self, vals):
        res = super(HRSalaryRules, self).write(vals)
        for rec in self:
            if not rec.salary_rule_id and (res.allowance_id.code or res.deduction.code):
                rec.create_salary_rule()
        return res

    def unlink(self):
        for rec in self:
            if rec.salary_rule_id and rec.salary_rule_id.structure_ids:
                raise ValidationError(_('Salary Rule is linked with Payroll Structure'))
            rec.salary_rule_id.unlink()
        return super(HRSalaryRules, self).unlink()

    def create_salary_rule(self):
        code = self.allowance_id.code or self.deduction_id.code
        apply_on = 'allowances_ids' if self.allowance_id else 'deductions_ids'
        data = {
            'name': self.allowance_id.name or self.deduction_id.name,
            'code': code,
            'sequence': 50 if self.allowance_id else 150,
            'quantity': 1,
            'category_id': 2 if self.allowance_id else 4,  # allowance
            'active': True,
            'appears_on_payslip': True,
            'company_id': 1,
            'condition_select': 'python',
            'condition_python': "result = True if len(contract.%s.filtered(lambda l: l.code == '%s')) > 0 else  False" % (apply_on,code,),
            'amount_select': 'code',
            'amount_python_compute': "result = contract.%s.filtered(lambda l: l.code == '%s').amount" % (apply_on,code,),
            'account_debit': self.account_id.id if self.allowance_id else False,
            'account_credit': self.account_id.id if self.deduction_id else False,
            'structure_ids': [(4, self.salary_structure_id.id, None)]
        }
        rule = self.env['hr.salary.rule'].create(data)
        self.salary_rule_id = rule.id

    
class HRSalaryAllowances(models.Model):
    _name = "hr.salary.allowances"
    _description = 'HR Salary Allowances'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    
    name = fields.Char('Name')
    code = fields.Char('Code')
    
    percentage_type_id = fields.Many2one('hr.salary.percentage.type','Percentage Type')
    percentage = fields.Float('Percentage')
    taxable = fields.Boolean('Taxable')
    
    rule_ids = fields.One2many('hr.salary.rules','allowance_id','Salary rules')
    lines = fields.One2many('hr.emp.salary.allowances', 'allowance_id', 'Employees/Contracts')
    head = fields.Char()
    note = fields.Text('Note')

    _sql_constraints = [
        ('code', 'unique(code)', "Code already exists "), ]
    
    def write(self, vals):
        res = super(HRSalaryAllowances, self).write(vals)
        for rec in self:
            for rule in rec.rule_ids:
                if not rule.salary_rule_id and rec.code:
                    rule.create_salary_rule()
        return res

    def unlink(self):
        for rec in self:
            if rec.lines:
                raise ValidationError(_('Employees/structures are linked with Record'))
            if rec.rule_ids:
                raise ValidationError(_('Salary Rule is linked with Payroll Structure'))
        return super(HRSalaryAllowances, self).unlink()
    

class HREmpSalaryAllowances(models.Model):
    _name = "hr.emp.salary.allowances"
    _description = 'HR Salary Allowances'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    
    contract_id = fields.Many2one('hr.contract','Contract')
    employee_id = fields.Many2one('hr.employee','Employee')
    allowance_id = fields.Many2one('hr.salary.allowances', 'Allowance')
    code = fields.Char(related='allowance_id.code')
    amount = fields.Float('Amount')


class HRSalaryDeductions(models.Model):
    _name = "hr.salary.deductions"
    _description = 'HR Salary Deductions'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    
    name = fields.Char('Name')
    code = fields.Char('Code')
    
    percentage_type_id = fields.Many2one('hr.salary.percentage.type', 'Percentage Type')
    percentage = fields.Float('Percentage')
    taxable = fields.Boolean('Taxable')
    
    rule_ids = fields.One2many('hr.salary.rules','deduction_id','Salary rules')
    lines = fields.One2many('hr.emp.salary.deductions','deduction_id','Employees/Contracts')
    head = fields.Char()
    note = fields.Text('Note')

    _sql_constraints = [
        ('code', 'unique(code)', "Code already exists "), ]

    def write(self, vals):
        res = super(HRSalaryDeductions, self).write(vals)
        for rec in self:
            for rule in rec.rule_ids:
                if not rule.salary_rule_id and rec.code:
                    rule.create_salary_rule()
        return res

    def unlink(self):
        for rec in self:
            if rec.lines:
                raise ValidationError(_('Employees/structures are linked with Record'))
            if rec.rule_ids:
                raise ValidationError(_('Salary Rule is linked with Payroll Structure'))
        return super(HRSalaryDeductions, self).unlink()


class HREmpSalaryDeductions(models.Model):
    _name = "hr.emp.salary.deductions"
    _description = 'HR Salary Allowances'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    
    contract_id = fields.Many2one('hr.contract', 'Contract')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    deduction_id = fields.Many2one('hr.salary.deductions', 'Deduction')
    code = fields.Char(related='deduction_id.code')
    amount = fields.Float('Amount')


class HRSalaryInputs(models.Model):
    _name = "hr.salary.inputs"
    _description = 'HR Salary Inputs'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char('Name')
    code = fields.Char('Code')
    input_type = fields.Selection([('alw','Allowance'),('ded','Deduction')],'Input Type')
    account_id = fields.Many2one('account.account', 'Account')

    salary_rule_id = fields.Many2one('hr.salary.rule', 'Salary Rule')
    note = fields.Text('Note')

    _sql_constraints = [
        ('code', 'unique(code)', "Code already exists "), ]

    @api.model
    def create(self, vals):
        res = super(HRSalaryInputs, self).create(vals)
        if res.code:
            res.create_salary_input_rule()
        return res

    def write(self, vals):
        res = super(HRSalaryInputs, self).write(vals)
        for rec in self:
            if not rec.salary_rule_id and rec.code:
                rec.create_salary_input_rule()

        return res

    def unlink(self):
        for rec in self:
            if rec.salary_rule_id and rec.salary_rule_id.structure_ids:
                raise ValidationError(_('Salary Rule is linked with Payroll Structure'))
            rec.salary_rule_id.unlink()
        return super(HRSalaryInputs, self).unlink()

    def create_salary_input_rule(self):
        lines = []
        line_data = {
            'name': self.name,
            'code': self.code,
        }
        lines.append([0, 0, line_data])
        data = {
            'name': self.name,
            'code': self.code,
            'sequence': 90 if self.input_type == 'alw' else 190,
            'quantity': 1,
            'category_id': 2 if self.input_type == 'alw' else 4,  # 2. Allowance,  4. Deduction
            'active': True,
            'appears_on_payslip': True,
            'company_id': 1,
            'condition_select': 'python',
            'condition_python': "result = True if inputs.%s and inputs.%s.amount > 0 else False" % (self.code,self.code),
            'amount_select': 'code',
            'amount_python_compute': "result = inputs.%s.amount" % (self.code,),
            'input_ids': lines,
            'account_debit': self.account_id.id if self.input_type == 'alw' else False,
            'account_credit': self.account_id.id if self.input_type == 'ded' else False,
        }
        self.salary_rule_id = self.env['hr.salary.rule'].create(data).id


class HREmpSalaryInputs(models.Model):
    _name = "hr.emp.salary.inputs"
    _description = "Employee Salary Inputs"
    _inherit = ['mail.thread']

    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, track_visibility='always')
    amount = fields.Float(string='Amount', required=True)
    description = fields.Text('Description')
    date = fields.Date('Effecting Date', required=True, track_visibility='onchange')
    input_id = fields.Many2one('hr.salary.inputs', string = 'Category', required=True,track_visibility='onchange')
    name = fields.Char(related='input_id.code')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('done', 'Paid'), ('cancel', 'Cancelled'), ],
                             'Status', default='draft', track_visibility='onchange')
    slip_id = fields.Many2one('hr.payslip', 'Pay Slip', ondelete='cascade', track_visibility='always')

    def inputs_validate(self):
        for rec in self:
            rec.write({'state': 'confirm'})

    def inputs_set_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def inputs_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    def inputs_approve(self):
        for rec in self:
            rec.write({'state': 'confirm'})

    def unlink(self):
        for input_id in self:
            if input_id.state != 'draft':
                raise ValidationError(_('You can only delete Salary Inputs in draft state .'))
        return super(HREmpSalaryInputs, self).unlink()

    @api.onchange('name')
    def onchange_faulty_pub(self):
        for rec in self:
            if rec.name == 'FINC':
                rec.amount = rec.employee_id.publications * rec.employee_id.rate_per_publication


class HRPayScaleCategory(models.Model):
    _name = 'hr.payscale.category'
    _description = 'HR PayScale Category'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active')
    scale_ids = fields.One2many('hr.payscale','scale_category_id', 'Scale(s)')
    
    
class HRPayScale(models.Model):
    _name = 'hr.payscale'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'HR PayScale'

    name = fields.Char('Grade', track_visibility='onchange')
    code = fields.Char('Code', track_visibility='onchange')
    basic_pay = fields.Float('Basic Pay')
    increment = fields.Float('Increment')
    stages = fields.Integer('Stages')
    last_limit = fields.Float('Last Limit')
    scale_category_id = fields.Many2one('hr.payscale.category','Category')

    # employee_ids = fields.One2many('hr.employee','payscale_id', 'Employee(s)')
    
    
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    payscale_id = fields.Many2one('hr.payscale', related='employee_id.payscale_id', string='Payscale', store=True)

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []
        rule_obj = self.env['hr.salary.rule']
        arrears_obj = self.env['hr.emp.salary.inputs']
        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        for contract in contracts:
            for rule in rule_obj.browse(sorted_rule_ids):
                if rule.input_ids:
                    for input in rule.input_ids:
                        arr_amt = ''
                        arr_ids = arrears_obj.search(
                            [('employee_id', '=', contract.employee_id.id), ('name', '=', input.code),
                             ('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'confirm')])
                        if arr_ids:
                            arr_amt = 0
                            for arr_id in arr_ids:
                                arr_amt += arr_id.amount
                        inputs = {
                            'name': input.name,
                            'code': input.code,
                            'contract_id': contract.id,
                            'amount': arr_amt or 0,
                        }
                        res += [inputs]
        return res
    
    @api.model
    def get_inputs2(self, contracts, date_from, date_to):
        res = []
        rule_obj = self.env['hr.salary.rule']
        arrears_obj = self.env['hr.salary.inputs']
        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        for contract in contracts:
            for rule in rule_obj.browse(sorted_rule_ids):
                if rule.input_ids:
                    for input in rule.input_ids:
                        arr_amt = ''
                        arr_ids = arrears_obj.search(
                            [('employee_id', '=', contract.employee_id.id), ('name', '=', input.code),
                             ('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'confirm')])
                        if arr_ids:
                            arr_amt = 0
                            for arr_id in arr_ids:
                                arr_amt += arr_id.amount
                        inputs = {
                            'name': input.name,
                            'code': input.code,
                            'contract_id': contract.id,
                            'amount': arr_amt or 0,
                        }
                        res += [inputs]
        return res

    @api.model
    def get_contract(self, employee, date_from, date_to):
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', 'in', ('draft','open')), '|', '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    
    structure_ids = fields.Many2many('hr.payroll.structure', 'hr_structure_salary_rule_rel', 'rule_id', 'struct_id', string='Salary Structures')