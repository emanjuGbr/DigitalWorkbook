# -*- coding: utf-8 -*-

from odoo import models, fields


class onedrive_object(models.Model):
    _name = "onedrive.object"
    _description = "Mapping between Odoo records and Onedrive directories."

    name = fields.Char()
    res_id = fields.Integer()
    onedrive_id = fields.Char()
