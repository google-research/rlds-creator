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

"""Base class for environments."""

import abc
import enum
from typing import Any, Dict, Optional

import dataclasses
import dm_env
import numpy as np

DMEnv = dm_env.Environment
TimeStep = dm_env.TimeStep
Image = np.ndarray
# Active keys and their values. For digital keys, e.g. a keyboard key, the value
# will be 1. For analog keys, e.g. from a gamepad, the values are floating point
# numbers (in the range [-1.0, 1.0] for stick axes and (0, 1.0] for buttons).
Keys = Dict[str, float]
Metadata = Dict[str, Any]


# Type of the controller.
class Controller(enum.Enum):
  DEFAULT = 1
  # A 3Dconnexion SpaceMouse. 6DOF and two buttons.
  SPACEMOUSE = 2


@dataclasses.dataclass
class UserInput:
  """Denotes the user input."""
  # Active keys and their values.
  keys: Keys
  # Type of the controller.
  controller: Controller = Controller.DEFAULT


@dataclasses.dataclass
class Camera:
  # 0-based index of the camera.
  index: int
  # Name of the camera; it may be empty.
  name: str = ''


class Environment(metaclass=abc.ABCMeta):
  """Base class for environments."""

  @abc.abstractmethod
  def env(self) -> DMEnv:
    """Returns the DM environment."""

  @abc.abstractmethod
  def keys_to_action(self, keys: Keys) -> Any:
    """Maps the pressed keys to an action in the environment."""

  def user_input_to_action(self, user_input: UserInput) -> Any:
    """Maps the user input to an action in the environment."""
    return self.keys_to_action(user_input.keys)

  @abc.abstractmethod
  def render(self) -> Image:
    """Returns the environment as an image."""

  def set_camera(self, index: int) -> Optional[Camera]:
    """Sets the camera to render images.

    Args:
      index: 0-based index of the camera.

    Returns:
      a Camera object that contains information about the camera or None if the
      camera cannot be set.
    """
    del index
    return None

  def metadata(self) -> Metadata:
    """Returns the metadata about the environment, e.g. generation seed."""
    return {}

  def step_info(self) -> Any:
    """Returns the auxiliary information of the last step."""
    return None
