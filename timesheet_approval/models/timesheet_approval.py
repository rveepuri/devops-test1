# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

from odoo import fields, api, models,_
from odoo.exceptions import UserError, ValidationError

import datetime
from odoo.tests import Form
from odoo.tools import float_compare, float_is_zero, float_repr, float_round, float_split, float_split_str
from odoo.osv import expression


class TimesheetApproval(models.Model):
    _name = "timesheet.approval"
    _rec_names_search = ['from_date','employee_id']

    from_date = fields.Date(string="Timesheet From")
    to_date = fields.Date(string="Timesheet To")
    timesheet_lines = fields.One2many('timesheet.approval.lines','timesheet_approval_id',string="Timesheet Approval Lines")
    user_id = fields.Many2one('res.users', string='Scheduler User', default=lambda self: self.env.user, required=True)
    employee_id = fields.Many2one('hr.employee',string="Employee")
    state = fields.Selection([('new','New'),('waiting_approval','Waiting For Approval'),('approved','Approved'),('reject','Refuse'),('invoice','Invoiced')],string="Status",default='new')
    timesheet_manager_id = fields.Many2one('res.users','Approval Manager')
    wages = fields.Float(string="Wages")
    per_day_amount = fields.Float(string="Day Amount")
    invoice_ref = fields.Many2one('account.move',string="Invoice")
    attachment = fields.Binary('Document', copy=False, tracking=True)


    def name_get(self):
        data = []
        for rec in self:
            data.append((rec.id, '%s / %s' % (rec.from_date, rec.to_date)))
        return data

    def action_timesheet_invoice(self):
        product = self.env['product.product'].search([('name','=','Time Sheet')])
        invoice = self.env['account.move'].create({
            'partner_id':self.user_id.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_line_ids':[(0,0,{'product_id':product.id,
                                      'name':self.employee_id.name,
                                      'quantity':sum(self.timesheet_lines.mapped('spend_time')),
                                      'price_unit':self.per_day_amount
            })]
        })
        self.invoice_ref = invoice
        self.write({'state':'invoice'})

    def button_open_invoices(self):
        ''' Redirect the user to the invoice(s) paid by this payment.
        :return:    An action on account.move.
        '''
        self.ensure_one()

        action = {
            'name': _("Timesheet Invoices"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
        }
        if len(self.invoice_ref) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.invoice_ref.id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', self.invoice_ref.ids)],
            })
        return action

    def submit_to_manager(self):
        self.write({'state':'waiting_approval'})
    def action_approved(self):
        self.write({'state':'approved'})
    def action_reject(self):
        self.write({'state':'reject'})
    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            self.employee_id = self.user_id.employee_id
            self.timesheet_manager_id = self.employee_id.timesheet_manager_id


    @api.onchange('from_date', 'to_date','employee_id')
    def onchange_from_date(self):
        if self.employee_id:
            for each in self.employee_id.contract_ids:
                self.wages = each.wage
                # diff = (self.to_date - self.from_date).days
                # days=diff
                # total_hours = days * self.employee_id.resource_calendar_id.hours_per_day
                # hours_per_week = each.hours_per_week
                self.per_day_amount = self.employee_id.hourly_cost
                # if not each.hourly_wage:
                #     per_day = wages/self.total_hours

            tasks_list = self.env['account.analytic.line'].sudo().search(
                [('date', '>=', self.from_date),('employee_id', '>=', self.employee_id.id),
                 ('date', '<=', self.to_date)])

        list = []
        for task in tasks_list:
            if task.task_id:
                data = (0, 0, {
                    'task_id': task.task_id.id,
                    'project_id': task.project_id.id,
                    'date': task.date,
                    'spend_time': task.unit_amount,
                    'name': task.name,
                    # 'wages': wages,
                    'date': task.date,
                })
                list.append(data)
        self.timesheet_lines = False
        self.timesheet_lines = list


class TimesheetApprovalLines(models.Model):
    _name = "timesheet.approval.lines"

    timesheet_approval_id =fields.Many2one('timesheet.approval')
    project_id = fields.Many2one('project.project',string="Project")
    task_id = fields.Many2one('project.task',string="Tasks")
    spend_time = fields.Float(string="Spend Hrs")
    total_amount = fields.Float(string="Total Amount",compute='_compute_total')
    date = fields.Date(string="Date")
    wages = fields.Float(string="Wages")
    per_day_amount = fields.Float(string="Day Amount")
    name = fields.Text(string="Description")





    def _compute_total(self):
        for each in self:
            each.total_amount = each.spend_time




class ProjectRole(models.Model):
    _name = "project.role"

    name = fields.Char(string="Role")
    cost = fields.Float(string="Cost")

