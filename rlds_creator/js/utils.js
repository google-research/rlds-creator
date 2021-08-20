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
 * @fileoverview Utility functions.
 */
goog.module('rlds_creator.utils');

const Option = goog.require('goog.ui.Option');
const Select = goog.require('goog.ui.Select');
const dom = goog.require('goog.dom');
const style = goog.require('goog.style');

/**
 * Returns the element with the specified ID or the element itself.
 *
 * @param {string|?Element} idOrEl Element or its ID.
 * @return {?Element}
 */
function getElement(idOrEl) {
  const el = typeof idOrEl === 'string' ? dom.getElement(idOrEl) : idOrEl;
  console.assert(el, {idOrEl});  // For debugging purposes.
  return el;
}

/**
 * Sets the value of a text field.
 *
 * @param {string|?Element} idOrEl Textfield element or its ID.
 * @param {string} value
 */
function setTextField(idOrEl, value) {
  /** @type {!MDLTextfieldElement} */ (dom.getParentElement(getElement(idOrEl)))
      .MaterialTextfield.change(value);
}

/**
 * (Un)checks a radio button.
 *
 * @param {string|?Element} idOrEl Radio button element or its ID.
 * @param {boolean=} check Whether to check or uncheck.
 */
function checkRadio(idOrEl, check = true) {
  const radio =
      /** @type {!MDLRadioElement} */ (dom.getParentElement(getElement(idOrEl)))
          .MaterialRadio;
  if (check) {
    radio.check();
  } else {
    radio.uncheck();
  }
}

/**
 * (Un)checks a checkbox.
 *
 * @param {string|?Element} idOrEl Checkbox element or its ID.
 * @param {boolean=} check Whether to check or uncheck.
 */
function checkCheckbox(idOrEl, check = true) {
  const radio =
      /** @type {!MDLCheckboxElement} */ (
          dom.getParentElement(getElement(idOrEl)))
          .MaterialCheckbox;
  if (check) {
    radio.check();
  } else {
    radio.uncheck();
  }
}

/**
 * Creates a select with the specified list of options.
 *
 * @param {string} id ID of the select.
 * @param {string|?Element} parentIdOrEl Parent element or its ID.
 * @param {!Array<{id: string, label: string}>} options List of options with
 *     their IDs and labels.
 * @return {!Select}
 */
function createSelect(id, parentIdOrEl, options) {
  const select = new Select('Select...');
  select.setId(id);
  select.render(getElement(parentIdOrEl));
  for (const option of options) {
    const label = option['label'] || option['id'];
    select.addItem(new Option(label, option['id']));
  }
  return select;
}

/**
 * Shows or hides the element with the specified ID.
 *
 * @param {string|?Element} idOrEl Element or its ID.
 * @param {boolean=} show True to show or false to hide.
 */
function showElement(idOrEl, show = true) {
  const el = getElement(idOrEl);
  if (style.isElementShown(el) != show) {
    style.setElementShown(el, show);
  }
}

/**
 * Hides an element.
 *
 * @param {string|?Element} idOrEl Element or its ID.
 */
function hideElement(idOrEl) {
  showElement(idOrEl, false);
}

/**
 * Sets the text content of the element with the specified ID.
 *
 * @param {string} id ID of the element.
 * @param {string|number} text Text content.
 */
function setTextContent(id, text) {
  dom.setTextContent(dom.getElement(id), text);
}

/**
 * Creates a non-numeric cell element.
 *
 * @param {string|!Element} value A DOM node or string.
 * @return {!HTMLTableCellElement} The resulting cell.
 */
function createNonNumericCell(value) {
  return dom.createDom(
      dom.TagName.TD, {'class': 'mdl-data-table__cell--non-numeric'}, value);
}

/**
 * Creates a numeric cell element.
 *
 * @param {number} value A numeric value.
 * @return {!HTMLTableCellElement} The resulting cell.
 */
function createNumericCell(value) {
  return dom.createDom(dom.TagName.TD, null, value.toString());
}

/**
 * Creates a checkbox with the specified text.
 *
 * @param {string} id ID of the checkbox.
 * @param {string} text Caption of the checkbox.
 * @return {!HTMLLabelElement} Parent element of the checkbox, i.e. the label.
 */
function createCheckbox(id, text) {
  const label = dom.createDom(dom.TagName.LABEL, {
    'class': 'mdl-checkbox mdl-js-checkbox mdl-js-ripple-effect',
    'for': id
  });
  const input = dom.createDom(
      dom.TagName.INPUT,
      {'type': 'checkbox', 'id': id, 'class': 'mdl-checkbox__input'});
  dom.append(
      label, input,
      dom.createDom(dom.TagName.SPAN, {'class': 'mdl-checkbox__label'}, text));
  return label;
}

/**
 * Returns true if the checkbox is checked.
 *
 * @param {string|?Element} idOrEl Checkbox element or its ID.
 * @return {boolean}
 */
function isChecked(idOrEl) {
  return /** @type {!HTMLInputElement} */ (getElement(idOrEl)).checked;
}

/**
 * Creates a material design icon.
 *
 * @param {string} name Name of the icon.
 * @return {!Element} an <i> element.
 */
function createIcon(name) {
  return dom.createDom(dom.TagName.I, {'class': 'material-icons'}, name);
}

/**
 * Creates a material switch.
 *
 * @param {string} id ID of the input element.
 * @param {boolean=} checked Initial state of the switch.
 * @return {!Element} the parent element (a label).
 */
function createSwitch(id, checked = false) {
  const label = dom.createDom(
      dom.TagName.LABEL, {'class': 'mdl-switch mdl-js-switch', 'for': id});
  const input = dom.createDom(
      dom.TagName.INPUT,
      {'type': 'checkbox', 'id': id, 'class': 'mdl-switch__input'});
  input.checked = checked;
  dom.append(
      label, input,
      dom.createDom(dom.TagName.SPAN, {'class': 'mdl-switch__label'}));
  return label;
}

exports = {
  checkCheckbox,
  checkRadio,
  createCheckbox,
  createIcon,
  createNonNumericCell,
  createNumericCell,
  createSelect,
  createSwitch,
  getElement,
  hideElement,
  isChecked,
  setTextContent,
  setTextField,
  showElement,
};
