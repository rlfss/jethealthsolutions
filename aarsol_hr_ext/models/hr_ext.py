import time
from datetime import date , datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT
from dateutil import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.osv import expression
import pdb


def parse_date(td):
	resYear = float(td.days)/365.0
	resMonth = (resYear - int(resYear))*365.0/30.0
	resDays = int((resMonth - int(resMonth))*30)
	resYear = int(resYear)
	resMonth = int(resMonth)
	return (resYear and (str(resYear) + "Y ") or "") + (resMonth and (str(resMonth) + "M ") or "") + (resMonth and (str(resDays) + "D") or "")


class HRJob(models.Model):
	_inherit = 'hr.job'
	
	section_id = fields.Many2one('hr.section', 'Section')


class HRSection(models.Model):
	_name = 'hr.section'
	_description = 'HR Section'
	
	name = fields.Char('Section Name')
	employee_ids = fields.One2many('hr.employee', 'section_id', 'Employees')


class HRCategory(models.Model):
	_name = 'hr.category'
	_description = 'HR Category'
	
	name = fields.Char('Category Name')
	employee_ids = fields.One2many('hr.employee', 'category_id', 'Employees')
	old_id = fields.Char('Old Id')


class HREmployeeMedical(models.Model):
	_name = 'hr.employee.medical'
	_description = 'Employee Medical'
	
	disease = fields.Char('Disease', required=1)
	appoinment_date = fields.Char('Appoinment Date')
	hospital = fields.Char('Hospital')
	employee_id = fields.Many2one('hr.employee', 'Employee')


class HREmployeeOperationArea(models.Model):
	_name = 'hr.employee.operation.area'
	_description = 'Emplyee Operation Areas'
	_inherit = ['mail.thread','mail.activity.mixin']
	
	name = fields.Char('Operation Area')
	code = fields.Char('Code')


class HREmployeeFamily(models.Model):
	_name = 'hr.employee.family'
	_description = 'Employee Family'
	
	name = fields.Char('Name of Family Member', required=1)
	relationship = fields.Char('Relationship with employee')
	phone_no = fields.Char('Contact No')
	employee_id = fields.Many2one('hr.employee', 'Employee')


class hr_experience(models.Model):
	_name = 'hr.experience'
	_description = 'HR Experience'


	@api.depends('start_date','end_date')
	def _total_experience_days(self):
		for rec in self:
			if rec.start_date and rec.end_date:
				start = datetime.strptime(str(rec.start_date),OE_DFORMAT)
				end = datetime.strptime(str(rec.end_date), OE_DFORMAT)
				delta = end - start
				rec.total_experience = parse_date(delta)
				
	name = fields.Char("Company Name")
	employee_id = fields.Many2one('hr.employee', string = 'Employee')
	position = fields.Char("Position")
	salary = fields.Float("Salary")
	currency = fields.Char("Currency")
	start_date = fields.Date('Start Date')
	end_date = fields.Date('End Date')
	total_experience = fields.Char(compute='_total_experience_days', string="Total Experience", help="Auto Calculated")
	reporting_to = fields.Char("Reporting To")
	reason_to_leave = fields.Text("Reason For Leaving")
	responsibilities = fields.Text("Responsibilities")


class HREmployeeAcademic(models.Model):
	_name = 'hr.employee.academic'
	_description = 'Employee Academics'
	
	degree_level = fields.Selection([('matric', 'Matric'), ('inter', 'Intermediate'),('undergraduate','Undergraduate'),('graduate','graduate'),('postgraduate','Postgraduate')], 'Degree Level', required=1)
	degree = fields.Char('Degree', required=1)
	year = fields.Char('Passing Year')
	board = fields.Char('Board Name')
	subjects = fields.Char('Subjects')
	total_marks = fields.Integer('Total Marks', required=1)
	obtained_marks = fields.Integer('Obtained Marks', required=1)
	employee_id = fields.Many2one('hr.employee', 'Employee')
