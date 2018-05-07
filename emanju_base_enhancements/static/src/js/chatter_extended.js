odoo.define('chatter_extended.Chatter', function (require) {
"use strict";

var Activity = require('mail.Activity');
var chat_mixin = require('mail.chat_mixin');
var ChatterComposer = require('mail.ChatterComposer');
var Followers = require('mail.Followers');
var ThreadField = require('mail.ThreadField');
var utils = require('mail.utils');

var concurrency = require('web.concurrency');
var config = require('web.config');
var core = require('web.core');
var Widget = require('web.Widget');
var Chatter = require('mail.Chatter');

var QWeb = core.qweb;

Chatter.include({
    _openComposer: function (options) {
        var self = this;
        var old_composer = this.composer;
        // create the new composer
        this.composer = new ChatterComposer(this, this.record.model, options.suggested_partners || [], {
            commands_enabled: false,
            context: this.context,
            input_min_height: 50,
            input_max_height: Number.MAX_VALUE, // no max_height limit for the chatter
            input_baseline: 14,
            is_log: options && options.is_log,
            record_name: this.record_name,
            default_body: old_composer && old_composer.$input && old_composer.$input.val(),
            default_mention_selections: old_composer && old_composer.mention_get_listener_selections(),
        });
        this.composer.on('input_focused', this, function () {
            this.composer.mention_set_prefetched_partners(this.mentionSuggestions || []);
        });
        this.composer.insertAfter(this.$('.o_chatter_topbar')).then(function () {
            // destroy existing composer
            if (old_composer) {
                old_composer.destroy();
            }
            if (!config.device.touch) {
                self.composer.focus();
            }
            self.composer.on('post_message', self, function (message) {
                self.fields.thread.postMessage(message).then(function () {
                    self._closeComposer(true);
                    if (self.postRefresh === 'always' || (self.postRefresh === 'recipients' && message.partner_ids.length)) {
                        self.trigger_up('reload');
                    }
                });
            });
            self.composer.on('need_refresh', self, self.trigger_up.bind(self, 'reload'));
            self.composer.on('close_composer', null, self._closeComposer.bind(self, true));

            self.$el.addClass('o_chatter_composer_active');
            self.$('.o_chatter_button_new_message, .o_chatter_button_log_note').removeClass('o_active');
            self.$('.o_chatter_button_new_message').toggleClass('o_active', !self.composer.options.is_log);
            self.$('.o_chatter_button_log_note').toggleClass('o_active', self.composer.options.is_log);
        });
		if (!self.composer.options.is_log){
			self.composer.$el.find('.o_composer_button_full_composer').trigger('click');
		}
		//self.composer.destroy();
    },
});

});
