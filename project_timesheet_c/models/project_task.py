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

    @api.onchange('user_ids')
    def _onchange_user_ids_roles(self):
        list = []
        if self.user_ids:
            for each in self.user_ids:
                    dict = (0,0,{
                        'user_id':each._origin.id,
                        'role_id':self.id
                    })
                    list.append(dict)
            self.users_roles = False
            self.users_roles=list


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


