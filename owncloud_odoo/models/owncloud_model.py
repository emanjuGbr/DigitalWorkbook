# -*- coding: utf-8 -*-

from odoo import models, fields


class owncloud_model(models.Model):
    _name = "owncloud.model"
    _description = "Mapping between Odoo models and Owncloud directories."

    name = fields.Char()
    owncloud_id = fields.Char()
