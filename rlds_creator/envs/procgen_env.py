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

"""Procgen environments."""

from typing import Optional

import gym
from gym import wrappers
import procgen

from rlds_creator import environment
from rlds_creator import gym_utils
from rlds_creator import input_utils
from rlds_creator import study_pb2

ProcgenSpec = study_pb2.EnvironmentSpec.Procgen

_DISTRIBUTION_MODE = {
    ProcgenSpec.DISTRIBUTION_EASY: 'easy',
    ProcgenSpec.DISTRIBUTION_HARD: 'hard',
    ProcgenSpec.DISTRIBUTION_EXTREME: 'extreme',
    ProcgenSpec.DISTRIBUTION_MEMORY: 'memory',
    ProcgenSpec.DISTRIBUTION_EXPLORATION: 'exploration',
}

# Special action.
_KEY_MAPPING = {'BUTTON0': 'D'}


class ProcgenEnvironment(gym_utils.GymEnvironment):
  """A Procgen environment."""

  def __init__(self, env_spec: study_pb2.EnvironmentSpec):
    args = env_spec.procgen
    distribution_mode = _DISTRIBUTION_MODE.get(args.distribution_mode)
    if not distribution_mode:
      raise ValueError('Unsupported distribution mode.')

    kwargs = {}
    if args.distribution_mode != ProcgenSpec.DISTRIBUTION_EXPLORATION:
      kwargs.update({
          'num_levels': args.num_levels,
          'start_level': args.start_level
      })
    if args.HasField('rand_seed'):
      kwargs['rand_seed'] = args.rand_seed

    timeout = env_spec.max_episode_steps
    env = gym.make(
        'procgen-{}-v0'.format(args.id),
        distribution_mode=distribution_mode,
        use_sequential_levels=args.use_sequential_levels,
        **kwargs)
    venv = env.unwrapped._venv
    self._combos = list(venv.combos)
    self._metadata = venv.options
    # Use time limit wrapper if the timeout different from maximum steps.
    if self._metadata.get('timeout', 0) != timeout:
      self._metadata['timeout'] = timeout
      env = wrappers.TimeLimit(env, timeout)
    super().__init__(env)

  def keys_to_action(self, keys: environment.Keys) -> Optional[int]:
    action = None
    max_len = -1
    keys = input_utils.apply_default_gamepad_mapping(keys)
    # Procgen uses upper case keys.
    keys = {key.upper(): value for key, value in keys.items()}
    keys = input_utils.get_mapped_keys(keys, _KEY_MAPPING)

    if 'RETURN' in keys:
      action = -1
    else:
      for i, combo in enumerate(self._combos):
        pressed = True
        for key in combo:
          if key not in keys:
            pressed = False

        if pressed and (max_len < len(combo)):
          action = i
          max_len = len(combo)

    return action

  def metadata(self) -> environment.Metadata:
    return self._metadata
