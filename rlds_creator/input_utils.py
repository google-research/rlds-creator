# coding=utf-8
# Copyright 2021 RLDSCreator Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for user input."""

from typing import Any, Dict, List, Optional, Tuple

from rlds_creator import environment

# Default mapping from left button cluster of a gamepad to the cursor keys. See
# https://www.w3.org/TR/gamepad/#dfn-standard-gamepad-layout.
DEFAULT_BUTTON_MAPPING = {
    'Button12': 'Up',
    'Button15': 'Right',
    'Button13': 'Down',
    'Button14': 'Left'
}

# Default mapping from the left stick of a gamepad to the cursor keys.
DEFAULT_AXIS_MAPPING = {'Axis0': ('Left', 'Right'), 'Axis1': ('Up', 'Down')}


def get_key_mapping(inverse_mapping: Dict[Any, List[str]]) -> Dict[str, Any]:
  """Returns the key mapping from the inverse mapping.

  Args:
    inverse_mapping: A mapping from the mapped input to the list of keys.

  Returns:
    a mapping from the keys to their mapped input.
  """
  mapped_keys = {}
  for mapped_key, keys in inverse_mapping.items():
    for key in keys:
      mapped_keys[key] = mapped_key
  return mapped_keys


def get_mapped_keys(keys: environment.Keys,
                    mapping: Dict[str, str]) -> environment.Keys:
  """Returns the keys applying the specified key mapping."""
  return {mapping.get(key, key): value for key, value in keys.items()}


def axes_to_keys(
    keys: environment.Keys,
    threshold: float = 0.5,
    mapping: Optional[Dict[str, Tuple[str, str]]] = None) -> environment.Keys:
  """Returns the keys that correspond to the values of the axes.

  Args:
    keys: Input keys that contain the axes values.
    threshold: Threshold to determine the mapped key. For a mapping (axis,
      neg_key, pos_key), the mapped key will be neg_key if the value of the axis
      is less than or equal to -threshold and pos_key if it is greater than or
      equal to +threshold.
    mapping: A list of mappings of the form (axis, neg_key, pos_key).

  Returns:
    Mapped keys. Their values will be 1.
  """
  mapping = mapping or DEFAULT_AXIS_MAPPING
  mapped_keys = {}
  for axis, (neg_key, pos_key) in mapping.items():
    value = keys.get(axis, 0)
    if value <= -threshold:
      mapped_keys[neg_key] = 1
    elif value >= threshold:
      mapped_keys[pos_key] = 1
  return mapped_keys


def apply_default_gamepad_mapping(keys: environment.Keys) -> environment.Keys:
  """Applies the default gamepad mappings to the keys."""
  keys = get_mapped_keys(keys, DEFAULT_BUTTON_MAPPING)
  return {**keys, **axes_to_keys(keys)}
