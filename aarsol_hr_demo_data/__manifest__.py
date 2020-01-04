{
	'name': 'AARSOL HR Demo Data',
	'version': '1.0',
	'category': 'Human Resources/Employees',
	'sequence': 6,
	'license': 'AGPL-3',
	'description': "This module adds the Demo Data for HR.",
	'author': 'Farooq',
	'website': 'http://www.aarsolerp.com/',
	'depends': ['base','hr','hr_recruitment','hr_attendance'],
	'data': [
		'data/hr_demo.xml',
		'data/hr_attendance_demo.xml',
	],
	'license': 'AGPL-3',
	'installable': True,
	'auto_install': False,
	'application': True,
}


