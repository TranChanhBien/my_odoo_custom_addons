from odoo import models, fields


class ProjectProject(models.Model):
    _inherit = "project.project"

    lark_project_guid = fields.Char(
        string="Lark Project ID",
        index=True
    )