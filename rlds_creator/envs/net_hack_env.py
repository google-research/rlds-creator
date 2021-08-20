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

"""NetHack environments."""

from typing import Optional

import gym
import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from rlds_creator import environment
from rlds_creator import gym_utils
from rlds_creator import input_utils
from rlds_creator import study_pb2

import nle

_MARGIN = 5  # Margin for the rendered images.


class NetHackEnvironment(gym_utils.GymEnvironment):
  """A NetHack environment."""

  def __init__(self, env_spec: study_pb2.EnvironmentSpec):
    # Default max episode steps in NLE is 5000.
    max_episode_steps = env_spec.max_episode_steps or 5000
    self._net_hack_env = gym.make(
        env_spec.net_hack.id, max_episode_steps=max_episode_steps)
    self._font = ImageFont.load_default()
    # Image size is set on first render() call.
    self._img_size = None
    super().__init__(self._net_hack_env)
    del self._renderer  # Not used.

  def render(self) -> environment.Image:
    env = self._net_hack_env
    # TODO(sertan): Add support for color and other attributes.
    grid = env.render(mode='ansi')
    # Also display the message to the user. In the observations, it is a fixed
    # size vector of numbers with the ordinal form of the characters.
    message = bytes(env.last_observation[env._message_index])
    grid += '\n\n' + message[:message.index(b'\0')].decode('utf-8')
    if self._img_size is None:
      # Dummy image to get the actual image size.
      img = Image.new('RGB', (1, 1))
      height, width = ImageDraw.Draw(img).multiline_textsize(
          grid, font=self._font, spacing=0)
      self._img_size = (height + 2 * _MARGIN, width + 2 * _MARGIN)
    img = Image.new('RGB', self._img_size, (255, 255, 255))
    ImageDraw.Draw(img).multiline_text((_MARGIN, _MARGIN),
                                       grid,
                                       font=self._font,
                                       fill=(0, 0, 0),
                                       spacing=0)
    return np.array(img)

  def keys_to_action(self, keys: environment.Keys) -> Optional[int]:
    keys = input_utils.get_mapped_keys(keys, input_utils.DEFAULT_BUTTON_MAPPING)
    for key in keys:
      # First matching action will be returned. NetHack doesn't have composite
      # actions.
      try:
        ch = ord(key)
        return self._net_hack_env._actions.index(ch)
      except:
        continue
    return None
