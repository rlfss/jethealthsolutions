from datetime import datetime

from odoo import models, fields, api

import io
import base64
import csv
import pdb

class hr_payslip_wps(models.TransientModel):
	_name = 'hr.payslip.wps'
	_description = 'WPS for Bank'

	filedata = fields.Binary('File')
	filename = fields.Char('Filename', size = 64, readonly=True)
	date = fields.Date('Date')


	def get_wps(self):
		slips_obj = self.env['hr.payslip']
		data = self.read([])[0]
		
		recs = slips_obj.search([('date_from','<=',self.date),('date_to','>=',self.date)])

		result = []
		result.append(['Sr#','Employee #','Scale','Name','Designation','Department','Joining Date',
			'Pay per Month','Increment','Arrears','Gross Pay','Adjustment','Tax','Net Amount','Account Number'])

		i = 1
		for rec in recs:
			arrear = 0
			gross = 0
			net = 0
			od = 0
			tax = 0
			increment = 0
			
			
			for line in rec.line_ids:
				# line.salary_rule_id.category_id.code
				if line.salary_rule_id.code == 'FINC':
					increment += line.total
				if line.salary_rule_id.code == 'NET':
					net += line.total
				if line.salary_rule_id.code == 'IT':
					tax += line.total
				if line.salary_rule_id.code == 'GROSS':
					gross += line.total
				if line.salary_rule_id.code == 'OD':
					od += line.total
				if line.salary_rule_id.code == 'ARS':
					arrear += line.total

			temp = []
			
			temp.append(str(i))
			temp.append(rec.employee_id.code)
			temp.append(rec.employee_id.payscale_id.name)
			temp.append(rec.employee_id.name)
			temp.append(rec.employee_id.job_title)
			temp.append(rec.employee_id.department_id.name)
			temp.append(rec.contract_id.date_start)
			
			temp.append(rec.contract_id.wage)
			temp.append(str(increment or '-'))
			temp.append(str(arrear or '-'))
			temp.append(str(gross))
			temp.append(str(od or '-'))
			temp.append(str(tax or '-'))
			
			temp.append(str(net))
			temp.append(str(rec.employee_id.bank_account_no))
			
			result.append(temp)
			i = i + 1

		fp = io.StringIO()
		writer = csv.writer(fp)
		for data in result:
			row = []
			for d in data:
				# if isinstance(d, str):
				# 	d = d.replace('\n',' ').replace('\t',' ')
				# 	try:
				# 		d = d.encode('utf-8')
				# 	except:
				# 		pass
				if d is False: d = None
				row.append(d)
			writer.writerow(row)

		fp.seek(0)
		data = fp.read()
		fp.close()
		
		out= base64.encodestring(data.encode(encoding='utf-8'))    #base64.encodestring(data)
		file_name = 'payroll_' + str(self.date)+'_wps.csv'

		self.write({'filedata':out, 'filename':file_name})
		
		return {
			'name':'WPS File',
			'res_model':'hr.payslip.wps',
			'type':'ir.actions.act_window',
			'view_type':'form',
			'view_mode':'form',
			'target':'new',
			'nodestroy': True,			
			'res_id': self.id,
		} 
