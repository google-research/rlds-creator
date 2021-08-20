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

/** @externs */

/**
 * Class constructor for Snackbar MDL component.
 * @unrestricted
 */
class MaterialSnackbar {
  /**
   * @param {?Element} element The element that will be upgraded.
   */
  constructor(element) {}

  /**
   * Show the snackbar.
   *
   * @param {?Object} data The data for the notification.
   */
  showSnackbar(data) {}
}


/** @type {!MaterialSnackbar|undefined} */
Element.prototype.MaterialSnackbar;

/**
 * An element which has been upgraded to a Textfield MDL component.
 * @extends {HTMLElement}
 */
class MDLTextfieldElement {}

/**
 * @type {!MaterialTextfield}
 */
MDLTextfieldElement.prototype.MaterialTextfield;

/**
 * Class constructor for Textfield MDL component.
 * @unrestricted
 */
class MaterialTextfield {
  /*
   * @param {HTMLElement} element The element that will be upgraded.
   */
  constructor(element) {}

  /**
   * Update text field value.
   *
   * @param {string} value The value to which to set the control (optional).
   */
  change(value) {}
}

/**
 * An element which has been upgraded to a DataTable MDL component.
 * @extends {HTMLTableElement}
 */
class MDLDataTableElement {}

/**
 * @type {!MaterialDataTable}
 */
MDLDataTableElement.prototype.MaterialDataTable;

/**
 * Class constructor for DataTable MDL component.
 * @unrestricted
 */
class MaterialDataTable {
  /*
   * @param {HTMLElement} element The element that will be upgraded.
   */
  constructor(element) {}

  /**
   * Creates a checkbox for a single or or multiple rows and hooks up the
   * event handling.
   *
   * @param {Element} row Row to toggle when checkbox changes.
   * @param {(Array<Object>|NodeList)=} rows Rows to toggle when checkbox
   *     changes.
   */
  createCheckbox_(row, rows) {}
}

/**
 * An element which has been upgraded to a Radio MDL component.
 * @extends {HTMLElement}
 */
class MDLRadioElement {}

/**
 * @type {!MaterialRadio}
 */
MDLRadioElement.prototype.MaterialRadio;

/**
 * Class constructor for Radio MDL component.
 * @unrestricted
 */
class MaterialRadio {
  /*
   * @param {HTMLElement} element The element that will be upgraded.
   */
  constructor(element) {}

  /**
   * Checks the radio button.
   */
  check() {}

  /**
   * Unchecks the radio button.
   */
  uncheck() {}
}

/**
 * An element which has been upgraded to a Checkbox MDL component.
 * @extends {HTMLElement}
 */
class MDLCheckboxElement {}

/**
 * @type {!MaterialCheckbox}
 */
MDLCheckboxElement.prototype.MaterialCheckbox;

/**
 * Class constructor for Checkbox MDL component.
 * @unrestricted
 */
class MaterialCheckbox {
  /*
   * @param {HTMLElement} element The element that will be upgraded.
   */
  constructor(element) {}

  /**
   * Checks the checkbox.
   */
  check() {}

  /**
   * Unchecks the checkbox.
   */
  uncheck() {}
}

/**
 * An element which has been upgraded to a Switch MDL component.
 * @extends {HTMLElement}
 */
class MDLSwitchElement {}

/**
 * @type {!MaterialSwitch}
 */
MDLSwitchElement.prototype.MaterialSwitch;

/**
 * Class constructor for Switch MDL component.
 * @unrestricted
 */
class MaterialSwitch {
  /*
   * @param {HTMLElement} element The element that will be upgraded.
   */
  constructor(element) {}

  /**
   * Checks the checkbox.
   */
  on() {}

  /**
   * Unchecks the checkbox.
   */
  off() {}
}

/**
 * An element which has been upgraded to a Slider MDL component.
 * @extends {HTMLElement}
 */
class MDLSliderElement {}

/**
 * @type {!MaterialSlider}
 */
MDLSliderElement.prototype.MaterialSlider;

/**
 * Class constructor for Slider MDL component.
 * @unrestricted
 */
class MaterialSlider {
  /*
   * @param {HTMLElement} element The element that will be upgraded.
   */
  constructor(element) {}

  /**
   * Update slider value.
   *
   * @param {number} value The value to which to set the control (optional).
   */
  change(value) {}
}

/**
 * An element which has been upgraded to a Progress MDL component.
 * @extends {HTMLElement}
 */
class MDLProgressElement {}

/**
 * @type {MaterialProgress}
 */
MDLProgressElement.prototype.MaterialProgress;

/**
 * Class constructor for Progress MDL component.
 * @unrestricted
 */
class MaterialProgress {
  /*
   * @param {HTMLElement} element The element that will be upgraded.
   */
  constructor(element) {}

  /**
   * Set the current progress of the progressbar.
   *
   * @param {number} p Percentage of the progress (0-100)
   */
  setProgress(p) {}

  /**
   * Set the current progress of the buffer.
   *
   * @param {number} p Percentage of the buffer (0-100)
   */
  setBuffer(p) {}
}

/**
 * Handler used in Material Design Light to register elements.
 */
const componentHandler = {
  /**
   * Upgrades a specific element rather than all in the DOM.
   *
   * @param {!Element} element The element we wish to upgrade.
   * @param {string=} jsClass Optional name of the class we want to upgrade to
   */
  upgradeElement(element, jsClass) {},
};

/**
 * Gamepad event type defined to avoid compilation errors.
 * @typedef {{
 *  gamepad: (!Gamepad),
 * }}
 */
let GamepadEvent;

/**
 * @method
 * @param {*} table
 * @return {google.visualization.DataTable}
 */
google.visualization.arrayToDataTable = function(table) {};
