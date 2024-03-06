# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

from odoo import fields, api, models,_
from odoo.exceptions import UserError, ValidationError

import datetime
from odoo.tests import Form
from odoo.tools import float_compare, float_is_zero, float_repr, float_round, float_split, float_split_str
from odoo.osv import expression
from dateutil.relativedelta import relativedelta
from odoo.tools import date_utils
class ProjectRole(models.Model):
    _name = "project.role"
    name = fields.Char(string="Role")
    cost = fields.Float(string="Cost")

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'
    _description = "Sales Advance Payment Invoice"

    def default_method_changed(self):
        if self.env.context.get('active_model') == 'project.task':
           return self.env['project.task'].browse(self.env.context.get('active_id')).project_sale_order_id
        else:
            return self.env.context.get('active_ids')
    def default_task_id_method_changed(self):
        if self.env.context.get('active_model') == 'project.task':
           return self.env['project.task'].browse(self.env.context.get('active_id'))
        else:
            return None
    sale_order_ids = fields.Many2many(
        'sale.order', default=default_method_changed)
    task_id = fields.Many2one('project.task',default=default_task_id_method_changed)
    date_custom = fields.Selection([('Previous_Month','Previous Month'),('yesterday','YesterDay'),('today','Today')],string='DateFilter')

    @api.onchange('date_custom')
    def date_custom_onchange(self):
        if self.date_custom == 'Previous_Month':
            today = fields.Date.today()
            last_month = today + relativedelta(months=-1)
            self.date_start_invoice_timesheet=last_month
        if self.date_custom == 'yesterday':
            today = fields.Date.today()
            previous_day = today + relativedelta(days=-1)
            self.date_start_invoice_timesheet=previous_day
            self.date_end_invoice_timesheet=today
        if self.date_custom == 'today':
            today = fields.Date.today()
            previous_day = today
            self.date_start_invoice_timesheet=previous_day
            self.date_end_invoice_timesheet=today

    def create_invoices(self):
        rec = super(SaleAdvancePaymentInv, self).create_invoices()
        invoice_id = False
        if rec.get('res_id'):
            invoice_id = self.env['account.move'].search([('id', '=', rec['res_id'])])
        if not invoice_id:
            invoice_id = self.env['account.move'].browse(rec['domain'][0][2][-1])
        if invoice_id:
            if self.task_id:
                invoice_id.project_task=self.task_id
            if self.invoicing_timesheet_enabled:
                invoice_id.from_date = self.date_start_invoice_timesheet
                invoice_id.to_date = self.date_end_invoice_timesheet
                list = []
                i = 0
                product = self.env['product.product']
                price = 0
                for each_task in self.env['sale.order'].search([('name', '=', invoice_id.invoice_origin)]).tasks_ids:
                    each_task.account_move = invoice_id
                    invoice_id.invoice_ticket = each_task
                    each_task.write({'kanban_state':'done'})
                    for each_employee in each_task.users_roles:
                    # for each_employee in each_task.timesheet_ids:
                        for invoice_line in invoice_id.invoice_line_ids:
                            if i == 0:
                               # each_task.timesheet_ids.filtered(lambda a: a.user_id == each_employee.user_id).invoiced_cc = True
                               # each_task.timesheet_ids.filtered(lambda a: a.user_id == each_employee.user_id and a.date >= self.date_start_invoice_timesheet and a.date <= self.date_end_invoice_timesheet).invoiced_cc = True
                               roles = 0
                               for task_line in each_task.timesheet_ids.filtered(lambda a: a.user_id == each_employee.user_id and a.date >= self.date_start_invoice_timesheet and a.date <= self.date_end_invoice_timesheet):
                                   task_line.invoiced_cc = True
                                   roles += task_line.unit_amount
                               invoice_line.name = each_employee.user_id.name
                               # roles = each_task.timesheet_ids.filtered(lambda a: a.user_id == each_employee.user_id)
                               # invoice_line.quantity = roles.unit_amount
                               invoice_line.quantity = roles
                               invoice_line.role = each_employee.role.id
                               invoice_line.price_unit = each_employee.role_cost
                               product = invoice_line.product_id
                               price = invoice_line.price_unit
                               continue
                        if i == 0 :
                            i += 1
                            continue

                    # if each_task.timesheet_ids.filtered(lambda a:a.user_id == each_employee.user_id and a.date >= self.date_start_invoice_timesheet and a.date <= self.date_end_invoice_timesheet):
                        roles =0
                        for each_lin in  each_task.timesheet_ids.filtered(lambda a:a.user_id == each_employee.user_id and a.date >= self.date_start_invoice_timesheet and a.date <= self.date_end_invoice_timesheet):
                            each_lin.invoiced_cc = True
                            # roles = each_task.timesheet_ids.filtered(lambda a: a.user_id == each_employee.user_id)
                            roles += each_lin.unit_amount
                        dict = self.env['account.move.line'].create({
                            'product_id': product.id,
                            'name':each_employee.user_id.name,
                            # 'quantity':roles.unit_amount,
                            'quantity':roles,
                            'role': each_employee.role.id,
                            'price_unit':each_employee.role_cost,
                            'move_id':invoice_id.id
                        })
                    # list.append(dict)
                # invoice_id.invoice_line_ids +=list
        return rec

class AccountInvoice(models.Model):
    _inherit = "account.move"
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    project_task = fields.Many2one('project.task')

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    role = fields.Many2one('project.role',string="Role")
class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    invoiced_cc = fields.Boolean(string="Invoice")
