from odoo import models, fields, api
import io
import json

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class DynamicEmployeeReport(models.Model):
    _name = "dynamic.employee.report"

    purchase_report = fields.Char(string="Employee Report")
    date_from = fields.Datetime(string="Date From")
    date_to = fields.Datetime(string="Date to")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    total_hours = fields.Float(string="Total Hours")
    wages = fields.Float(string="Wages")
    per_day = fields.Float(string="Hour Amount")
    hours_per_week = fields.Float(string="Hour/Week")
    report_type = fields.Selection([
        ('report_by_order', 'Report By Order'),
        ('report_by_product', 'Report By Product')], default='report_by_order')

    @api.model
    def purchase_report(self, option):
        report_values = self.env['dynamic.employee.report'].search(
            [('id', '=', option[0])])
        data = {

            'report_type': report_values.report_type,
            'model': self,
        }
        if report_values.date_from:
            data.update({
                'date_from': report_values.date_from,
            })
        if report_values.date_to:
            data.update({
                'date_to': report_values.date_to,
            })
        # filters = self.get_filter(option)
        # report = self._get_report_values(data)
        lines = self._get_report_values(data).get('PURCHASE')


        return {
            'name': "Employee Orders",
            'type': 'ir.actions.client',
            'tag': 's_r',
            'orders': data,
            # 'filters': filters,
            'report_lines': lines,
        }
    def get_filter(self, option):
        data = self.get_filter_data(option)
        filters = {}
        if data.get('report_type') == 'report_by_order':
            filters['report_type'] = 'Report By Order'
        return filters

    def get_filter_data(self, option):
        r = self.env['dynamic.employee.report'].search([('id', '=', option[0])])
        default_filters = {}
        filter_dict = {
            'report_type': r.report_type,
        }
        filter_dict.update(default_filters)
        return filter_dict
    def _get_report_sub_lines(self, data, report, date_from, date_to):
        report_sub_lines = []

        if data.get('report_type') == 'report_by_order':
            # query = """SELECT * FROM purchase_order"""
            # query = """SELECT a.partner_id,a.name FROM purchase_order a inner join purchase_order_line b on a.order_line= b.order_id
           #  query = """SELECT a.partner_id,a.name,b.product_id,b.product_qty,b.price_unit FROM purchase_order a inner join purchase_order_line b on a.id = b.order_id
           # """
            query = """SELECT a.partner_id,a.name,a.id FROM purchase_order a where state='purchase'"""

            self._cr.execute(query)
            report_by_order = self._cr.dictfetchall()

            for values in report_by_order:

                partial_values_list = []
                query_line = """SELECT b.product_id,b.product_qty,b.price_unit,b.price_subtotal FROM purchase_order_line b where order_id=%s""" % values['id']
                self._cr.execute(query_line)
                report_by_order_lines = self._cr.dictfetchall()
                for new_table in report_by_order_lines:
                    partial_values_list.append(new_table)
                    new_table['product_id'] = self.env['product.product'].browse(new_table['product_id']).name
                values.update({'Lines':partial_values_list})
                values['partner_id'] = self.env['res.partner'].browse(values['partner_id']).name
                report_sub_lines.append(values)
        return report_sub_lines


    def _get_report_values(self, data):
        docs = data['model']
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        report = ['Report By Order']
        if data.get('report_type'):
            report_res = self._get_report_sub_lines(data, report, date_from, date_to)
        else:
            report_res = self._get_report_sub_lines(data, report, date_from,
                                                    date_to)
        return {
            'doc_ids': self.ids,
            'docs': docs,
            'PURCHASE': report_res,
        }