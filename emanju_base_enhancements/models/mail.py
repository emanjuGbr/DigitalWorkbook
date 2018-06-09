# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class MailFollowers(models.Model):
    _inherit = 'mail.followers'

    @api.model
    def _add_follower_command(self, res_model, res_ids, partner_data,
                              channel_data, force=True):
        """ Please update me
        :param force: if True, delete existing followers before creating new
                      one using the subtypes given in the parameters
        """
        generic = []
        specific = {}
        # Check context and by pass autofollow up on record
        if 'mail_post_autofollow' in self._context and self._context.get(
                'mail_post_autofollow'):
            return generic, specific
        force_mode = force or (
                all(partner_data.values()) and all(channel_data.values()))
        existing = {}  # {res_id: follower_ids}
        p_exist = {}  # {partner_id: res_ids}
        c_exist = {}  # {channel_id: res_ids}

        # Search existing followers to record
        followers = self.sudo().search([
            '&',
            '&', ('res_model', '=', res_model), ('res_id', 'in', res_ids),
            '|', ('partner_id', 'in', list(partner_data)),
            ('channel_id', 'in', list(channel_data))])

        if force_mode:
            followers.unlink()
        else:
            for follower in followers:
                existing.setdefault(follower.res_id, list()).append(follower)
                if follower.partner_id:
                    p_exist.setdefault(follower.partner_id.id, list()).append(
                        follower.res_id)
                if follower.channel_id:
                    c_exist.setdefault(follower.channel_id.id, list()).append(
                        follower.res_id)

        default_subtypes, _internal_subtypes, external_subtypes = \
            self.env['mail.message.subtype'].default_subtypes(res_model)

        if force_mode:
            # Search employee list from Users
            employee_pids = self.env['res.users'].sudo().search(
                [('partner_id', 'in', list(partner_data)),
                 ('share', '=', False)]).mapped('partner_id').ids
            for pid, data in partner_data.items():
                if not data:
                    if pid not in employee_pids:
                        partner_data[pid] = external_subtypes.ids
                    else:
                        partner_data[pid] = default_subtypes.ids
            for cid, data in channel_data.items():
                if not data:
                    channel_data[cid] = default_subtypes.ids

        # create new followers, batch ok
        gen_new_pids = [pid for pid in partner_data if pid not in p_exist]
        gen_new_cids = [cid for cid in channel_data if cid not in c_exist]
        # Prepare list to update record with followers
        for pid in gen_new_pids:
            generic.append([0, 0, {'res_model': res_model, 'partner_id': pid,
                                   'subtype_ids': [(6, 0, partner_data.get(
                                       pid) or default_subtypes.ids)]}])
        for cid in gen_new_cids:
            generic.append([0, 0, {'res_model': res_model, 'channel_id': cid,
                                   'subtype_ids': [(6, 0, channel_data.get(
                                       cid) or default_subtypes.ids)]}])

        # create new followers, each document at a time because of existing
        # followers to avoid erasing
        if not force_mode:
            for res_id in res_ids:
                command = []
                doc_followers = existing.get(res_id, list())

                new_pids = set(partner_data) - set(
                    [sub.partner_id.id for sub in doc_followers if
                     sub.partner_id]) - set(gen_new_pids)
                new_cids = set(channel_data) - set(
                    [sub.channel_id.id for sub in doc_followers if
                     sub.channel_id]) - set(gen_new_cids)

                # subscribe new followers
                for new_pid in new_pids:
                    command.append((0, 0, {
                        'res_model': res_model,
                        'partner_id': new_pid,
                        'subtype_ids': [(6, 0, partner_data.get(
                            new_pid) or default_subtypes.ids)],
                    }))
                for new_cid in new_cids:
                    command.append((0, 0, {
                        'res_model': res_model,
                        'channel_id': new_cid,
                        'subtype_ids': [(6, 0, channel_data.get(
                            new_cid) or default_subtypes.ids)],
                    }))
                if command:
                    specific[res_id] = command
        return generic, specific
