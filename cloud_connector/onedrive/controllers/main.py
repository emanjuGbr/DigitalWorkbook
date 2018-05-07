# -*- coding: utf-8 -*-

import logging
import werkzeug

from odoo.http import Controller, route, request

_logger = logging.getLogger(__name__)


class one_drive_token(Controller):

    @route('/one_drive_token', type='http', auth='user', website='False')
    def login_to_onedrive(self, code=False, session_state=False):
        """Simple controller that handles incoming token"""
        request.env['res.config.settings'].create_onedrive_session(code=code)
        request.env['res.config.settings'].search_drive_id()

        config_action = request.env.ref('onedrive.onedrive_config_action')
        url = "/web#view_type=form&model=onedrive.config&action={}".format(
            config_action and config_action.id or ''
        )

        return werkzeug.utils.redirect(url)
