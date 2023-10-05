# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

from odoo import fields, api, models,_
from odoo.exceptions import UserError, ValidationError

import datetime
from odoo.tests import Form
from odoo.tools import float_compare, float_is_zero, float_repr, float_round, float_split, float_split_str
from odoo.osv import expression


class ProjectEmployeeOverhead(models.Model):
    _name = "employee.overhead"

    employee_id = fields.Many2one('hr.employee',string="Employee")
    employee_multiple_ids = fields.Many2many('hr.employee','employees',string="Employee")
    detailed_lines = fields.One2many('employee.overhead.lines','over_id',string="Detailed")
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    total_hours = fields.Float(string="Total Hours")
    wages = fields.Float(string="Wages")
    per_day = fields.Float(string="Hour Amount")
    hours_per_week = fields.Float(string="Hour/Week")


    # def name_get(self):
    #     result = []
    #     for bank in self:
    #         name = bank.from_date
    #         result.append(name)
    #     return result


    @api.onchange('from_date', 'to_date', 'employee_id')
    def onchange_from_date(self):
        if not self.employee_id:
                tasks_list = self.env['account.analytic.line'].sudo().search(
                    [('date', '>=', self.from_date),
                     ('date', '<=', self.to_date)])
        else:
            if self.employee_id:
                for each in self.employee_id.contract_ids:
                    self.wages = each.wage
                    # self.total_hours = (self.to_date - self.from_date).days
                    diff = (self.to_date - self.from_date).days
                    days=diff
                    # self.total_hours = days * 8 // 3600
                    # self.total_hours = days * 8
                    self.total_hours = days * self.employee_id.resource_calendar_id.hours_per_day
                    self.hours_per_week = each.hours_per_week
                    self.per_day = each.hourly_wage
                    if not each.hourly_wage:
                        self.per_day = self.wages/self.total_hours

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
                    'role_amount':sum(task.task_id.users_roles.filtered(lambda a:a.user_id == task.user_id).mapped('role_cost'))
                })
                list.append(data)
        self.detailed_lines = False
        self.detailed_lines = list


class ProjectOverheadLines(models.Model):
    _name = "employee.overhead.lines"

    over_id =fields.Many2one('employee.overhead')
    project_id = fields.Many2one('project.project',string="Project")
    task_id = fields.Many2one('project.task',string="Tasks")
    spend_time = fields.Float(string="Spend Hrs")
    role_amount = fields.Float(string="Role Amount")
    total_amount = fields.Float(string="Total Amount",compute='_compute_total')
    date = fields.Date(string="Date")



    def _compute_total(self):
        for each in self:
            each.total_amount = each.spend_time *each.role_amount