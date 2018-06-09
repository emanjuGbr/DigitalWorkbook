# -*- coding: utf-8 -*-

import json
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ir_attachment(models.Model):
    _inherit = "ir.attachment"

    last_sync_datetime = fields.Datetime(string=u"Time of last update")
    for_delete = fields.Boolean(default=False, string=u"Marked for delete")
    for_sync = fields.Boolean(default=True, string=u"Marked for sync.")
    active = fields.Boolean(default=True, string=u"Active")

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        """Allow to read records marked to delete by using the "show_for_delete"
        context keyword."""
        if 'for_delete' not in fields:
            fields = fields + ['for_delete']
        result = super(ir_attachment, self).read(fields=fields, load=load)
        if self._context.get('show_for_delete', False):
            result = [a for a in result if not a.get('for_delete')]
        return result

    @api.multi
    def unlink(self):
        """Deactivate attachments and mark for delete or unlink marked ones."""
        self.check('unlink')
        for_delete = self.filtered(lambda a: a.for_delete)
        mark_for_delete = self - for_delete
        values = {
            'for_delete': True,
            'active': False,
        }
        mark_for_delete.write(values)
        result = super(ir_attachment, for_delete).unlink()
        return result

    @api.multi
    def copy(self, default=None):
        """Do not allow to copy attachments marked to delete."""
        self.check('write')
        if self.for_delete:
            raise UserError("Can't copy attachments marked to delete.")
        return super(ir_attachment, self).copy(default)

    @api.multi
    def send_to_cloud(self):
        """Base method for uploading attachments to a cloud storage."""
        raise NotImplementedError

    @api.multi
    def synchronize(self):
        """Upload or remove marked attachments."""
        for record in self:
            if record.for_delete:
                _logger.info("Trying to delete ir.attachment {}".format(record.id))
                try:
                    if record.type == "url":
                        record.remove_attachment_from_cloud()
                    record.unlink()
                except Exception as e:
                    _logger.critical(u"Can't delete attachment in cloud id:{}; Reason {}".format(record.id, e))
            elif record.type == "binary":
                url = record.send_to_cloud()
                _logger.info("Replacing attachment id:{} with url {}".format(record.id, url))
                store_fname = record.store_fname
                record.store_fname = False
                record._file_delete(store_fname)
                record.datas = False
                record.datas_fname = False
                record.type = "url"
                record.url = url
                record.last_sync_datetime = fields.Datetime.now()

    @api.multi
    def remove_attachment_from_cloud(self):
        """Remove linked file from a cloud storage."""
        raise NotImplementedError

    @api.multi
    def attachments_checker(self):
        """Unmark attachments for synchronization to avoid uploading
        of system files."""
        mime_types = json.loads(self.env['ir.config_parameter'].get_param('not_sync_mime_types', '{}'))
        for attachment in self:
            not_sync = (
                attachment.mimetype in mime_types.values() and
                not attachment.res_model or
                attachment.name.startswith('/') or
                attachment.url and attachment.url.startswith('/') or
                attachment.res_model == "ir.module.module"
            )
            if not_sync:
                attachment.for_sync = False

    @api.model
    def cron_synchronize_attachments(self):
        """Cron for synchronization with a cloud storage."""
        attachments = self.with_context(show_for_delete=True).env['ir.attachment'].search(
            ['|', ('active', '=', True), ('active', '=', False)],
            order='last_sync_datetime ASC',
        )
        attachments.attachments_checker()
        attachments_for_sync = attachments.filtered(lambda record: record.for_sync)
        attachments_for_sync.synchronize()
