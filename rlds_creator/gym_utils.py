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

"""Gym utilities."""

from typing import Any

from acme import wrappers
import gym
from rlds_creator import environment
from rlds_creator import gym_renderer


class InfoWrapper(gym.Wrapper):
  """Wrapper that provides access to the information of the last step."""

  def __init__(self, env):
    super().__init__(env)
    self._step_info = None

  def reset(self):
    self._step_info = None
    return super().reset()

  def step(self, action):
    observation, reward, done, info = super().step(action)
    self._step_info = info
    return observation, reward, done, info

  def step_info(self) -> Any:
    """Returns the auxiliary information of the last step."""
    return self._step_info


class GymEnvironment(environment.Environment):
  """An Environment that is backed by a Gym Env."""

  def __init__(self, env: gym.Env):
    # We wrap the Gym environment to access the step info.
    self._gym_env = InfoWrapper(env)
    self._env = wrappers.gym_wrapper.GymWrapper(self._gym_env)
    self._renderer = gym_renderer.GymRenderer(self._gym_env)

  def env(self) -> environment.DMEnv:
    return self._env

  def render(self) -> environment.Image:
    return self._renderer.render()

  def step_info(self) -> Any:
    return self._gym_env.step_info()
