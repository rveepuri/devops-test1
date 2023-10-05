# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#
# Please note that these reports are not multi-currency !!!
#

import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv.expression import AND, expression
from psycopg2 import sql

from odoo import api, tools, fields, models

class EmployeePurchaseReport(models.Model):
    _name = "employee.purchase.report"
    _description = "Employee Purchase Report"
    _auto = False
    _order = 'date desc'

    name = fields.Char("Description", readonly=True)
    user_id = fields.Many2one("res.users", string="User", readonly=True)
    project_id = fields.Many2one("project.project", string="Project", readonly=True)
    task_id = fields.Many2one("project.task", string="Task", readonly=True)
    ancestor_task_id = fields.Many2one("project.task", string="Ancestor Task", readonly=True)
    employee_id = fields.Many2one("hr.employee", string="Employee", readonly=True)
    manager_id = fields.Many2one("hr.employee", "Manager", readonly=True)
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    department_id = fields.Many2one("hr.department", string="Department", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True)
    date = fields.Date("Date", readonly=True)
    amount = fields.Monetary("Amount", readonly=True)
    unit_amount = fields.Float("Hours Spent", readonly=True)
    wages = fields.Float("Wages", readonly=True)
    total_hours = fields.Float("Total Hours", readonly=True)
    per_day = fields.Float("Per Day", readonly=True)
    role_cost = fields.Float("Role Amount", readonly=True)
    wages  = fields.Float("wages", readonly=True)
    total_amount  = fields.Float("Total Amount", readonly=True)
    loss_amount  = fields.Float("Loss Amount", readonly=True)
    role = fields.Many2one('project.role', string="Role",readonly=True)

    @property
    def _table_query(self):
        return "%s %s %s" % (self._select(), self._from(), self._where())

    @api.model
    def _select(self):
        return """
              SELECT
                  A.id AS id,
                  A.name AS name,
                  A.create_date AS date,
                  A.user_id AS user_id,
                  A.project_id AS project_id,
                  A.task_id AS task_id,
                  A.ancestor_task_id AS ancestor_task_id,
                  A.employee_id AS employee_id,
                  A.manager_id AS manager_id,
                  A.company_id AS company_id,
                  A.department_id AS department_id,
                  A.currency_id AS currency_id,
                  A.amount AS amount,
                  A.role AS role,
                  A.role_cost AS role_cost,
                  A.wages  AS wages,
                  A.unit_amount*A.role_cost  AS total_amount,
                  A.wages-(A.unit_amount*A.role_cost)  AS loss_amount,
                  A.unit_amount AS unit_amount
          """

    @api.model
    def _from(self):
        return "FROM account_analytic_line A"

    @api.model
    def _where(self):
        return "WHERE A.project_id IS NOT NULL"

    @api.model
    def _get_view_cache_key(self, view_id=None, view_type='form', **options):
        """The override of _get_view changing the time field labels according to the company timesheet encoding UOM
        makes the view cache dependent on the company timesheet encoding uom"""
        key = super()._get_view_cache_key(view_id, view_type, **options)
        return key + (self.env.company.timesheet_encode_uom_id,)

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type in ["pivot", "graph"] and self.env.company.timesheet_encode_uom_id == self.env.ref(
                "uom.product_uom_day"):
            arch = self.env["account.analytic.line"]._apply_time_label(arch, related_model=self._name)
        return arch, view

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("CREATE or REPLACE VIEW {} as ({})").format(
                sql.Identifier(self._table),
                sql.SQL(self._table_query)
            )
        )