# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

from odoo import fields, api, models,_
from odoo.exceptions import UserError, ValidationError

import datetime
from odoo.tests import Form
from odoo.tools import float_compare, float_is_zero, float_repr, float_round, float_split, float_split_str
from odoo.osv import expression


class ProjectTask(models.Model):
    _inherit = "project.task"


    users_roles = fields.One2many('role.users','role_id',string="Assignees Role")
    account_move = fields.Many2one('account.move',string="Invoice")
    celer_account_moves = fields.One2many('account.move','project_task')
    invoice_ticket_ids = fields.Integer(string="Invoices",compute='compute_invoices_timesheet')
    invoice_ticket_tickets = fields.One2many('account.move', 'invoice_ticket')

    def action_view_invoices(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_invoice_type')
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'name': 'Invoices',
            'view_mode': 'tree,form',
            'views': [(False, "list"), (False, "form")],
            'domain': [('id', 'in', self.project_id.sale_order_id.invoice_ids.ids)],
        }
        return action



    def compute_invoices_timesheet(self):
        for each in self:
            # each.invoice_ticket_ids = each.project_id.invoice_count
            each.invoice_ticket_ids = len(each.invoice_ticket_tickets)
            each._invoice_invoice_colors()

    @api.depends('project_id')
    def _invoice_invoice_colors(self):
        # if self.project_id.invoice_count > 0:
        if len(self.invoice_ticket_tickets) > 0:
            self.color = 10

    @api.onchange('user_ids')
    def _onchange_user_ids_roles(self):
        list = []
        if self.user_ids:
            for each in self.user_ids:
                if not self.users_roles.filtered(lambda a: a.user_id == each._origin):
                    self.env['role.users'].create({
                        'user_id':each._origin.id,
                        'role_id':self.id
                    })
                    # dict = (0,0,{
                    #     'user_id':each._origin.id,
                    #     'role_id':self.id
                    # })
                    # list.append(dict)
                    # self.users_roles = False
                    # if not self.users_roles.filtered(lambda a:a.user_id == each._origin):
            # self.users_roles+=list


    def project_manager_get(self):
        if self.project_id:
            return self.project_id.user_id
    # project_manager = fields.Many2one('res.users',default=project_manager_get)
    project_manager = fields.Many2one('res.users', string='Super Admin', default=lambda self: self.env.user, required=True)
    project_leader= fields.Many2one('res.users',string="Project Manager")
    to_approval = fields.Boolean(string="To approval")
    approved = fields.Boolean(string="approved")
    rejected = fields.Boolean(string="approved")

    def action_for_approval(self):
        self.stage_id = self.env['project.task.type'].search([('project_ids','=',self.project_id.id),('name','=','To Approval')]).id
        self.to_approval = True
        # self.env['project.task.type'].search([('project_ids', '=', self.project_id.id), ('name', '=', 'Approved')])
        mail_template = self.env.ref('project_timesheet_c.mail_template_timesheet_approval')
        # body_html_content = "<p>Inprocess Quality Check Process is Rejected for %s !</p><br>%s" % (
        #     self.name, self.body_message)



        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        body = """<html>
                                       <head></head>
                                     <body>
                                        <p>Dear """ + self.project_manager.name + """,<br>
                                           Here is the Approval Timesheet <br> Timesheet :""" + self.name + """. <br>
                                           Project Name:""" + self.project_id.name + """.<br>
                                           Login URL :""" + current_url + """
                                       </p>
                                       </body>
                                     </html>
                                     """
        values = {
            'body_html': body,
        }
        mail_template.email_from = self.project_leader.login
        # mail_template.email_from = 'mounika@nhclindia.com'
        mail_template.reply_to = self.project_leader.login
        # mail_template.reply_to = 'mounika@nhclindia.com'
        mail_template.email_to = self.project_manager.login
        pdf_file = self.env['ir.actions.report']._render_qweb_pdf("hr_timesheet.timesheet_report_task", self.id)
        new_template = self.env['ir.attachment'].create({
            'name': "Timesheet.pdf",
            'datas': base64.b64encode(pdf_file[0]),
            'res_model': 'project.task',
            'res_id': self.id,
        })
        if not self.env["mail.followers"].search([('res_id','=',self.id),('partner_id','=',self.project_leader.partner_id.id)]):
            self.env["mail.followers"].create(
                {
                    "res_model": "project.task",
                    "res_id": self.id,
                    "partner_id": self.project_leader.partner_id.id,
                    # "subtype_ids": [(4, new_job_application_mt.id)],
                }
            )
        if not self.env["mail.followers"].search([('res_id','=',self.id),('partner_id','=',self.project_manager.partner_id.id)]):

            self.env["mail.followers"].create(
                {
                    "res_model": "project.task",
                    "res_id": self.id,
                    "partner_id": self.project_manager.partner_id.id,
                    # "subtype_ids": [(4, new_job_application_mt.id)],
                }
            )
        # mail_template.attachment_ids=False
        mail_template.attachment_ids = new_template
        # mail_template.email_cc = self.email_cc
        mail_template.send_mail(self.id, force_send=True, email_values=values)
        return
    def action_approved(self):
        self.approved = True
        self.stage_id = self.env['project.task.type'].search([('project_ids', '=', self.project_id.id), ('name', '=', 'Approved')])


    def action_rejected(self):
            self.to_approval = False
            # self.to_approval = False
            self.stage_id = self.env['project.task.type'].search([('project_ids', '=', self.project_id.id), ('name', '=', 'New')])



class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    role = fields.Many2one('project.role', string="Role",compute='_compute_project_role_id',store=True)
    role_cost = fields.Float(string="Cost",compute='_compute_project_role_id',store=True)
    wages = fields.Float(string="Wages",compute='_compute_project_role_id',store=True)

    @api.depends('user_id','employee_id')
    def _compute_project_role_id(self):
        for each in self:
            each.role =False
            each.role_cost =0.0
            each.wages =0.0
            for each_emp in each.employee_id:
                wages = 0
                for each_c in each.employee_id.contract_ids:
                    wages = each_c.wage
                each.wages = wages
                role_line = each.task_id.users_roles.filtered(lambda a: a.user_id == each_emp.user_id)
                role_cost = sum(role_line.mapped('role_cost'))
                each.role_cost = role_cost
                each.role = role_line.role



    def _domain_project_ids(self):
        # domain = [('allow_timesheets', '=', True)]
        domain = [('id', '=', self.env['project.project'].search([]).mapped('task_ids').search([('user_ids','=',self.env.user.id)]).mapped('project_id').ids)]
        if not self.user_has_groups('hr_timesheet.group_timesheet_manager'):
            return expression.AND([domain,
                ['|', ('privacy_visibility', '!=', 'followers'), ('message_partner_ids', 'in', [self.env.user.partner_id.id])]
            ])
        return domain

    project_id = fields.Many2one(
        'project.project', 'Project', domain=_domain_project_ids, index=True,
        compute='_compute_project_id', store=True, readonly=False)



class RoleUsers(models.Model):
    _name = "role.users"

    def _default_users_list(self):
        print('dfgdfdf')
        return [('id', 'in', self.role_id.user_ids.ids)]


    #
    # def _employee_ids_domain(self):
    #     # employee_ids is considered a safe field and as such will be fetched as sudo.
    #     # So try to enforce the security rules on the field to make sure we do not load employees outside of active companies
    #     return [('company_id', 'in', self.env.company.ids + self.env.context.get('allowed_company_ids', []))]


    role_id = fields.Many2one('project.task')
    role = fields.Many2one('project.role', string="Role")
    role_cost = fields.Float(string="Cost")
    user_id = fields.Many2one('res.users',string="Assignees")

    @api.onchange('role')
    def _onchange_role(self):
        if self.role:
            self.role_cost = self.role.cost
        else:
            self.role_cost =0


class ProjectProject(models.Model):
    _inherit = "project.project"

    invoice_ids  = fields.Integer(string="Invoices",compute='compute_invoice_ids')
    invoice_project_ids = fields.One2many('account.move','invoice_move')
    # invoice_count_all = fields.Integer(string="Invoice",compute_invoice_ids)

    def action_view_invoices(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_invoice_type')
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'name': 'Invoices',
            'view_mode': 'tree,form',
            'views': [(False, "list"), (False, "form")],
            'domain': [('id', 'in', self.sale_order_id.invoice_ids.ids)],
        }
        return action

    def compute_invoice_ids(self):
        for each in self:
            each._invoice_invoice_colors()
            # each.invoice_ids = each.invoice_count
            each.invoice_ids = sum(each.mapped('task_ids').mapped('invoice_ticket_ids'))

    def _invoice_invoice_colors(self):
        # if self.invoice_count >0:
        for each in  self:
            # for each_task in  each
            # if self.invoice_count_all >0:
            if sum(each.mapped('task_ids').mapped('invoice_ticket_ids')) >0:
                self.color = 10

    def action_project_invoices(self):
        action = self.env['ir.actions.act_window']._for_xml_id('hr_timesheet.act_hr_timesheet_line_by_project')
        action['display_name'] = _("%(name)s's Timesheets", name=self.name)
        return action


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_move = fields.Many2one('project.project')
    invoice_ticket = fields.Many2one('project.task')




