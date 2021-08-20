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

"""Atari environments."""

import gym

from rlds_creator import environment
from rlds_creator import gym_utils
from rlds_creator import input_utils
from rlds_creator import study_pb2

import os
from atari_py import games
# This path should point to the directory containing the ROMs.
games._games_dir = (
    os.environ.get('ATARI_GAMES_DIR') or
    '/usr/local/lib/python3.8/dist-packages/atari_py/atari_roms')

_KEY_MAPPING = input_utils.get_key_mapping({
    ord('w'): ['w', 'Up'],
    ord('a'): ['a', 'Left'],
    ord('s'): ['s', 'Down'],
    ord('d'): ['d', 'Right'],
    ord(' '): [' ', 'Button0'],  # Fire or action.
})


class AtariEnvironment(gym_utils.GymEnvironment):
  """An Atari environment."""

  def __init__(self, env_spec: study_pb2.EnvironmentSpec):
    # Sticky actions use v0.
    version = 'v0' if env_spec.atari.sticky_actions else 'v4'
    env = gym.make('{}-{}'.format(env_spec.atari.id, version))
    self._keys_to_action = env.get_keys_to_action()
    super().__init__(env)

  def keys_to_action(self, keys: environment.Keys) -> int:
    # See third_party/py/gym/envs/atari/atari_env.py.
    keys = input_utils.apply_default_gamepad_mapping(keys)
    keys = tuple(
        sorted([_KEY_MAPPING[key] for key in keys if key in _KEY_MAPPING]))
    return self._keys_to_action.get(keys, 0)
