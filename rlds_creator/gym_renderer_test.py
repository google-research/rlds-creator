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

"""Tests for the Gym renderer."""

from absl.testing import absltest
import gym
from gym import envs
from rlds_creator import gym_renderer


class GymRendererTest(absltest.TestCase):

  def test_render(self):
    # Create a sample (Mujoco) environment.
    env = gym.make('Ant-v3')
    env.reset()

    renderer = gym_renderer.GymRenderer(env)
    image = renderer.render()
    self.assertEqual(image.shape, (500, 500, 3))


if __name__ == '__main__':
  absltest.main()
