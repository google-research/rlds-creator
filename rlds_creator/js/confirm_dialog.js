// Copyright 2021 RLDSCreator Authors.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @fileoverview Material design confirmation dialog.
 */
goog.module('rlds_creator.confirmDialog');

const EventType = goog.require('goog.ui.Component.EventType');
const dom = goog.require('goog.dom');
const events = goog.require('goog.events');

/**
 * Material design confirmation dialog.
 */
class ConfirmDialog {
  constructor(content, title = 'Confirm') {
    /** @const @private {!HTMLDialogElement} */
    this.dialog_ = dom.createDom(dom.TagName.DIALOG, {'class': 'mdl-dialog'});
    /** @private {?function(boolean): boolean} */
    this.callback_ = null;
    events.listen(this.dialog_, EventType.CLOSE, e => {
      if (this.callback_) {
        if (this.callback_(this.dialog_.returnValue == 'accept')) {
          dom.removeNode(this.dialog_);
        } else {
          e.preventDefault();
        }
      }
    });
    const acceptButton = dom.createDom(
        dom.TagName.BUTTON, {'type': 'button', 'class': 'mdl-button'}, 'Yes');
    events.listen(
        acceptButton, events.EventType.CLICK,
        e => this.dialog_.close('accept'));
    const rejectButton = dom.createDom(
        dom.TagName.BUTTON, {'type': 'button', 'class': 'mdl-button'}, 'No');
    events.listen(
        rejectButton, events.EventType.CLICK,
        e => this.dialog_.close('reject'));
    // We add the reject button first to make it the default option.
    dom.append(
        this.dialog_,
        dom.createDom(dom.TagName.H4, {'class': 'mdl-dialog__title'}, title),
        dom.createDom(
            dom.TagName.DIV, {'class': 'mdl-dialog__content'}, content),
        dom.createDom(
            dom.TagName.DIV, {'class': 'mdl-dialog__actions'}, rejectButton,
            acceptButton));
  }

  /**
   * Shows the confirmation dialog as modal. This is a non-blocking operation.
   *
   * @param {function(boolean):boolean} callback Function that will be called
   * with a boolean value indicating whether the user accepted the confirmation
   * or not. It should return false to prevent dialog from closing.
   */
  showModal(callback) {
    this.dialog_.returnValue = 'reject';
    this.callback_ = callback;
    dom.appendChild(document.body, this.dialog_);
    this.dialog_.showModal();
  }
}

exports = {ConfirmDialog};
