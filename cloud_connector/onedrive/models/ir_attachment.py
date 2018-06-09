# -*- coding: utf-8 -*-

import logging
import re
import string

from odoo import models, fields, api, registry

try:
    from .onedrive_service import onedrivesdk
except ImportError:
    pass  # ImportError logged in onedrive_service

_logger = logging.getLogger(__name__)


def increment_name_counter(s):
    """Handle duplicated names"""
    s = s.split('.')
    if len(s) > 1:
        name, ext = '.'.join(s[:-1]), '.' + s[-1]
    else:
        name, ext = s[-1], ''
    counter = int((re.findall(r'\((\d+)\)$', name) + ['0'])[0])
    name = re.sub(r' \(\d+\)', '', name)
    res = '{} ({}){}'.format(name, counter + 1, ext)
    return res


def remove_illegal_characters(s):
    valid_chars = set("-_.() {}{}".format(string.ascii_letters, string.digits))
    return ''.join(filter(lambda c: c in valid_chars, s))


def mkdir(client, drive, parent, name):
    """Make directory on onedrive"""
    _logger.debug(
        'Trying to create directory with name "%s" in "%s" on drive "%s"',
        name, parent, drive,
    )
    if isinstance(parent, str):
        parent = client.item(drive=drive, id=parent)
    existing = {i.name for i in parent.children.get()}
    name = remove_illegal_characters(name)
    while name in existing:
        name = increment_name_counter(name)
    i = onedrivesdk.Item()
    i.name = name
    i.folder = onedrivesdk.Folder()
    res = parent.children.add(i)
    _logger.debug('Directory created with id "%s"', res.id)
    return res.id


class ir_attachment(models.Model):
    _inherit = "ir.attachment"

    onedrive_id = fields.Char("OneDrive ID")

    @api.model
    def find_or_create_root_directory(self, client):
        """Find or create Odoo root directory on OneDrive"""
        Config = self.env['res.config.settings']
        drive = Config.get_param('onedrive_drive_id', 'me')
        res_id = Config.get_param('onedrive_root_dir_id', '')
        if not res_id:
            res_id = mkdir(client, drive, 'root', 'Odoo')
            Config.set_param('onedrive_root_dir_id', res_id)

        return res_id

    @api.multi
    def find_or_create_model_directory(self, client, root_id):
        """Find or create directory for model of related object"""
        self.ensure_one()
        Config = self.env['res.config.settings']
        drive = Config.get_param('onedrive_drive_id', 'me')
        model = self.env['onedrive.model'].search(
            [('name', '=', self.res_model)],
            limit=1,
        )
        if model:
            return client.item(id=model.onedrive_id)

        res_id = mkdir(client, drive, root_id, self.env[self.res_model]._description)

        values = {
            'name': self.res_model,
            'onedrive_id': res_id,
        }
        self.env['onedrive.model'].create(values)

        return res_id

    @api.multi
    def find_or_create_object_directory(self, client, model_dir_id):
        """Find or create directory for related object"""
        self.ensure_one()
        Config = self.env['res.config.settings']
        drive = Config.get_param('onedrive_drive_id', 'me')

        obj = self.env['onedrive.object'].search(
            [('name', '=', self.res_model), ('res_id', '=', self.res_id)],
            limit=1,
        )
        if obj:
            return client.item(id=obj.onedrive_id)

        rec = self.env[self.res_model].browse(self.res_id)
        name = '{} {}'.format(rec.name_get()[0][1], rec.id)
        res = mkdir(client, drive, model_dir_id, name)

        values = {
            'name': self.res_model,
            'res_id': self.res_id,
            'onedrive_id': res,
        }
        self.env['onedrive.object'].create(values)
        return client.item(id=res)

    @api.multi
    def upload_file(self, client, target_dir):
        """Upload file to OneDrive"""
        self.ensure_one()
        if self.onedrive_id:
            res = client.item(id=self.onedrive_id)
        else:
            name = self.datas_fname
            existing = {i['name'] for i in target_dir.children.get()._prop_list}
            while name in existing:
                name = increment_name_counter(name)
            res = target_dir.children[name].upload(
                self._full_path(self.store_fname),
            )
            self.onedrive_id = res.id
        return res

    @api.multi
    def send_to_cloud(self, client=False):
        """Send attachment to cloud and create necessary folders"""
        self.ensure_one()
        client = self.env['onedrive.client'].get_client()

        local_path = self._full_path(self.store_fname)

        _logger.debug('Uploading attachment with id %s from "%s"', self.id, local_path)
        root_dir = self.find_or_create_root_directory(client)
        model_dir = self.find_or_create_model_directory(client, root_dir)
        object_dir = self.find_or_create_object_directory(client, model_dir)
        res_file = self.upload_file(client, object_dir)

        download_url = client.item(id=res_file.id).create_link('view').post().link.web_url
        _logger.debug('Uploaded attachment with id %s to "%s"', self.id, download_url)

        return download_url

    @api.multi
    def remove_attachment_from_cloud(self, client=None):
        """Removes linked file from server. Exceptions are covered in base synchronize"""
        self.ensure_one()
        client = self.env['onedrive.client'].get_client()
        if self.onedrive_id:
            client.item(id=self.onedrive_id).delete()
            _logger.info("Removed file {} from cloud; linked ir.attachment: {}".format(
                self.name, self.id,
            ))

    @api.model
    def cron_synchronize_attachments(self):
        """Inherited base cron with passing client"""
        super(ir_attachment, self).cron_synchronize_attachments()

    @api.model
    def cron_update_from_onedrive(self):
        """Cron for updatig files from OneDrive."""
        with api.Environment.manage():
            with registry(self._cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self._uid, self._context)

                client = self.env['onedrive.client'].get_client()

                ObjectMap = new_env['onedrive.object']
                _logger.debug("Getting updates from Onedrive.")

                for obj in ObjectMap.search([]):
                    od_items = client.item(id=obj.onedrive_id).children.get()
                    od_items_set = {i['id'] for i in od_items._prop_list}

                    attachments = new_env['ir.attachment'].search([
                        ('onedrive_id', '!=', False),
                        ('res_model', '=', obj.name),
                        ('res_id', '=', obj.res_id),
                    ])
                    attachments_set = set(attachments.mapped('onedrive_id'))

                    to_delete = attachments_set - od_items_set
                    to_create = od_items_set - attachments_set

                    _logger.debug(
                        "Trying to fetch updates for object {} {}".format(
                            obj.name, obj.res_id,
                        )
                    )
                    created = new_env['ir.attachment']
                    for oid in to_create:
                        od_item = client.item(id=oid).get()
                        download_url = client.item(id=oid).create_link('view').post().link.web_url
                        values = {
                            'name': od_item.name,
                            'res_model': obj.name,
                            'res_id': obj.res_id,
                            'type': 'url',
                            'onedrive_id': oid,
                            'url': download_url,
                        }
                        created |= new_env['ir.attachment'].create(values)

                    _logger.debug(
                        "Created: {}".format(', '.join(created.mapped('name'))),
                    )

                    to_delete = attachments.filtered(
                        lambda a: a.onedrive_id in to_delete
                    )
                    _logger.debug(
                        "Deleted: {}".format(', '.join(to_delete.mapped('name'))),
                    )
                    to_delete.unlink()
                    new_cr.commit()
