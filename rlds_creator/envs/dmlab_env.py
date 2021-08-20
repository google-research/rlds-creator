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

"""DMLab environments."""

from absl import logging
import dm_env
from dm_env import specs
import numpy as np
from rlds_creator import environment
from rlds_creator import input_utils
from rlds_creator import study_pb2

import deepmind_lab


def _action(*entries):
  """Helper function for defining an action."""
  return np.array(entries, dtype=np.intc)


_KEYS_TO_ACTIONS = {
    'Left': _action(-20, 0, 0, 0, 0, 0, 0),
    'Right': _action(20, 0, 0, 0, 0, 0, 0),
    'Down': _action(0, 10, 0, 0, 0, 0, 0),
    'Up': _action(0, -10, 0, 0, 0, 0, 0),
    'a': _action(0, 0, -1, 0, 0, 0, 0),
    'd': _action(0, 0, 1, 0, 0, 0, 0),
    'w': _action(0, 0, 0, 1, 0, 0, 0),
    's': _action(0, 0, 0, -1, 0, 0, 0),
    'Control': _action(0, 0, 0, 0, 1, 0, 0),
    ' ': _action(0, 0, 0, 0, 0, 1, 0),
    'c': _action(0, 0, 0, 0, 0, 0, 1)
}

_BUTTON_MAPPING = {'Button3': ' ', 'Button0': 'c', 'Button1': 'Control'}
_AXIS_MAPPING = {'Axis2': ('a', 'd'), 'Axis3': ('w', 's')}


class DmLabWrapper(dm_env.Environment):
  """Wrapper for a DM Lab."""

  def __init__(self, lab: deepmind_lab.Lab, obs_name: str):
    """Creates a wrapper.

    Args:
      lab: a Lab.
      obs_name: Name of the Lab observation, e.g. RGB_INTERLEAVED, that will be
        used as the observation of the environment.
    """
    self._lab = lab
    self._obs_name = obs_name
    self._observation_spec = None
    # Pick the observation spec that matches the specified name.
    for spec in lab.observation_spec():
      if spec['name'] == obs_name:
        self._observation_spec = specs.Array(
            shape=spec['shape'], dtype=spec['dtype'])
        break
    logging.info('Observation spec %r', self._observation_spec)
    # Convert Lab action specs into an environment action spec.
    minimum = []
    maximum = []
    action_specs = lab.action_spec()
    for spec in action_specs:
      logging.info('Action spec %r', spec)
      minimum.append(spec['min'])
      maximum.append(spec['max'])
    # This currently assumes that the action specs match the mapping defined
    # above, i.e. there are 7 of them.
    self._action_spec = specs.BoundedArray((len(action_specs),),
                                           np.int,
                                           minimum=minimum,
                                           maximum=maximum)

  def _observation(self):
    """Returns the environment observation."""
    return self._lab.observations()[self._obs_name]

  def reset(self) -> dm_env.TimeStep:
    self._lab.reset()
    return dm_env.restart(self._observation())

  def step(self, action: np.ndarray) -> dm_env.TimeStep:
    reward = self._lab.step(action)
    if self._lab.is_running():
      return dm_env.transition(reward=reward, observation=self._observation())
    else:
      return dm_env.termination(reward=reward, observation=self._observation())

  def action_spec(self) -> specs.BoundedArray:
    return self._action_spec

  def observation_spec(self) -> specs.Array:
    return self._observation_spec


class DmLabEnvironment(environment.Environment):
  """A DMLab environment."""

  def __init__(self, env_spec: study_pb2.EnvironmentSpec):
    # TODO(sertan): These should go to the envrionment spec.
    mixer_seed = 0
    dmlab_env_settings = {
        'mixerSeed': str(mixer_seed),
        'width': '256',
        'height': '256',
    }
    level_name = 'contributed/dmlab30/' + env_spec.dmlab.id
    self._lab = deepmind_lab.Lab(level_name, [
        'DEBUG.MAZE.LAYOUT',
        'RGB_INTERLEAVED',
    ], dmlab_env_settings, 'software')
    self._env = DmLabWrapper(self._lab, 'RGB_INTERLEAVED')

  @classmethod
  def keys_to_action(cls, keys: environment.Keys) -> np.ndarray:
    keys = input_utils.apply_default_gamepad_mapping(keys)
    keys = input_utils.get_mapped_keys(keys, _BUTTON_MAPPING)
    keys = {
        **keys,
        **input_utils.axes_to_keys(keys, threshold=0.5, mapping=_AXIS_MAPPING)
    }
    # We combine the action vectors of the pressed keys.
    action = np.zeros((7,), dtype=np.intc)
    for key in keys:
      if key in _KEYS_TO_ACTIONS:
        action += _KEYS_TO_ACTIONS[key]
    return action

  def env(self) -> environment.DMEnv:
    return self._env

  def render(self) -> environment.Image:
    return self._lab.observations()['RGB_INTERLEAVED']
