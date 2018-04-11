# -*- coding: utf-8 -*-

from odoo import models, fields


class onedrive_model(models.Model):
    _name = "onedrive.model"
    _description = "Mapping between Odoo models and Onedrive directories."

    name = fields.Char()
    onedrive_id = fields.Char()
