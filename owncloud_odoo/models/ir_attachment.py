# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ir_attachment(models.Model):
    _inherit = "ir.attachment"

    owncloud_id = fields.Char()

    @api.multi
    def send_to_cloud(self):
        """Send an attachment to Owncloud."""
        self.ensure_one()
        Owncloud = self.env["owncloud.client"]
        cloud_path = self.build_cloud_path()
        local_path = self._full_path(self.store_fname)
        self.owncloud_id, self.owncloud_path, url = Owncloud.upload_file(cloud_path, local_path)
        return url

    @api.multi
    def remove_attachment_from_cloud(self):
        """Remove an attachment from Owncloud."""
        self.ensure_one()
        Owncloud = self.env["owncloud.client"]
        cloud_path = self.build_cloud_path()
        Owncloud.remove_file(cloud_path[:-1], self.owncloud_id)

    @api.multi
    def build_cloud_path(self):
        """Build path using a model description and an object name."""
        self.ensure_one()
        Owncloud = self.env["owncloud.client"]
        if self.res_model and self.res_id:
            path = Owncloud.get_object_directory_path(self.res_model, self.res_id)
        else:
            path = ['Undefined', self.datas_fname]
        path.append(self.datas_fname)
        return path

    @api.model
    def cron_update_from_owncloud(self):
        """Cron for updating files from Owncloud."""
        ModelMap = self.env['owncloud.model']
        ObjectMap = self.env['owncloud.object']
        Attachment = self.env['ir.attachment']
        Owncloud = self.env["owncloud.client"]
        model_dirs = Owncloud.list_root()
        _logger.debug(u"Getting updates from Owncloud.")
        for model_owncloud_id, model_path in model_dirs.items():
            model_map = ModelMap.search(
                [('owncloud_id', '=', model_owncloud_id)], limit=1,
            )
            _logger.debug(
                u"Trying to find matching model directory with id: {}, {} object found.".format(
                    model_owncloud_id, model_map,
                )
            )
            if not model_map:
                continue
            object_dirs = Owncloud.list_path(model_path)
            for object_owncloud_id, object_data in object_dirs.items():
                object_map = ObjectMap.search(
                    [('owncloud_id', '=', object_owncloud_id)], limit=1,
                )
                _logger.debug(
                    u"Trying to find matching object directory with id: {}, {} object found.".format(
                        model_owncloud_id, model_map,
                    )
                )
                if not object_map:
                    continue
                _, object_path = object_data
                files = Owncloud.list_path(object_path)
                attachments = Attachment.search(
                    [
                        ('res_model', '=', object_map.name),
                        ('res_id', '=', object_map.res_id),
                        ('owncloud_id', '!=', False),
                    ]
                )
                files_set = set(files)
                attachments_set = set(attachments.mapped('owncloud_id'))
                missing_attachments = files_set - attachments_set
                deleted_attachments = attachments_set - files_set
                _logger.debug("Missing attachments: {}".format(missing_attachments))
                _logger.debug("Deleted attachments: {}".format(deleted_attachments))
                for file_owncloud_id in missing_attachments:
                    file_name, file_path = files[file_owncloud_id]
                    values = {
                        'name': file_name,
                        'res_model': object_map.name,
                        'res_id': object_map.res_id,
                        'type': 'url',
                        'url': Owncloud.get_url(file_path),
                        'owncloud_id': file_owncloud_id,
                    }
                    _logger.debug(u"Trying to create an attachment using following values: {}".format(values))
                    Attachment.create(values)
                attachments.filtered(
                    lambda a: a.owncloud_id in deleted_attachments
                ).unlink()
