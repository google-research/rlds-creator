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

"""Renderer for an OpenAI Gym environment."""

import gym

from rlds_creator import renderer


class GymRenderer(renderer.Renderer):
  """Renderer for an OpenAI Gym environment."""

  def __init__(self, env: gym.Env):
    self._env = env

  def render(self, **kwargs) -> renderer.Image:
    # We simply call the render method using the RGB mode.
    return self._env.render(mode='rgb_array', **kwargs)
