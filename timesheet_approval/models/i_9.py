# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

from odoo import fields, api, models,_
from odoo.exceptions import UserError, ValidationError

import datetime
from odoo.tests import Form
from odoo.tools import float_compare, float_is_zero, float_repr, float_round, float_split, float_split_str
from odoo.osv import expression


class EmployeeI9(models.Model):
    _name = "employee.i.9"
    _rec_names_search = ['from_date','employee_id']


    user_id = fields.Many2one('res.users', string='Scheduler User', default=lambda self: self.env.user, required=True)
    employee_id = fields.Many2one('hr.employee',string="Employee")
    state = fields.Selection([('new','New'),('waiting_approval','Waiting For Approval'),('verified','Verified'),('reject','Refuse')],string="Status",default='new')
    timesheet_manager_id = fields.Many2one('res.users','Verified Manager')
    attachment = fields.Binary('Document', copy=False, tracking=True)
    date_of_joining = fields.Date(string="Joining Date")
    email_id = fields.Char(string="Employee Email")
    id_proff_no = fields.Char(string="Passport No")
    name = fields.Char(string="Ref")
    ref_person = fields.Char(string="Ref Person")
    create_date = fields.Date(string="Initied Date", default=fields.Date.today())
    completion_date = fields.Date(string="Completion Date")
    attachment_ids = fields.One2many('ir.attachment', 'res_id', string="Attachments")
    # supported_attachment_ids = fields.Many2many(
    #     'ir.attachment', string="Attach File", compute='_compute_supported_attachment_ids')

    # @api.depends('leave_type_support_document', 'attachment_ids')
    # def _compute_supported_attachment_ids(self):
    #     for holiday in self:
    #         holiday.supported_attachment_ids = holiday.attachment_ids
    #         # holiday.supported_attachment_ids_count = len(holiday.attachment_ids.ids)

    def name_get(self):
        data = []
        for rec in self:
            data.append((rec.name, '%s' % (rec.employee_id.name)))
        return data

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.date_of_joining = self.employee_id.first_contract_date
            self.email_id = self.employee_id.private_email
            self.id_proff_no = self.employee_id.passport_id

    def submit_to_manager(self):
        self.write({'state': 'waiting_approval'})

    def action_approved(self):
        self.write({'state': 'verified'})

    def action_reject(self):
        self.write({'state': 'reject'})