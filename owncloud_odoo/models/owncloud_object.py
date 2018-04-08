# -*- coding: utf-8 -*-

from odoo import models, fields


class owncloud_object(models.Model):
    _name = "owncloud.object"
    _description = "Mapping between Odoo records and Owncloud directories."

    name = fields.Char()
    res_id = fields.Integer()
    owncloud_id = fields.Char()
