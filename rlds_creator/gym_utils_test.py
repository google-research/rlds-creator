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

"""Tests for rlds_creator.gym_utils."""

from typing import Any

from absl.testing import absltest
import gym
from gym import spaces
import mock

from rlds_creator import environment
from rlds_creator import gym_utils


class ConcreteGymEnvironment(gym_utils.GymEnvironment):

  def keys_to_action(self, keys: environment.Keys) -> Any:
    return None


class GymUtilsTest(absltest.TestCase):

  @mock.patch.object(gym, 'Env', autospec=True)
  def test_info_wrapper(self, env):
    wrapped = gym_utils.InfoWrapper(env)
    self.assertIsNone(wrapped.step_info())

    steps = [(1, 0.1, False, {'a': 123}), (2, 0.2, True, {'b': 456})]
    env.step.side_effect = steps

    # Advance two steps. The step info should match that of the last step.
    self.assertEqual(steps[0], wrapped.step(None))
    self.assertEqual({'a': 123}, wrapped.step_info())

    self.assertEqual(steps[1], wrapped.step(None))
    self.assertEqual({'b': 456}, wrapped.step_info())

    wrapped.reset()
    # Step info should be reset as well.
    self.assertIsNone(wrapped.step_info())

  @mock.patch.object(gym, 'Env', autospec=True)
  def test_gym_environment(self, env):
    env.observation_space = spaces.Discrete(4)
    env.action_space = spaces.Discrete(2)
    env.reset.return_value = 1
    env.step.return_value = (2, 0.1, False, {'a': 123})

    image = [[[128, 0, 0], [0, 0, 128]]]
    env.render.return_value = image

    gym_env = ConcreteGymEnvironment(env)
    denv = gym_env.env()
    timestep = denv.reset()
    self.assertEqual(1, timestep.observation)
    self.assertTrue(timestep.first())

    timestep = gym_env.env().step(0)
    self.assertEqual(2, timestep.observation)
    self.assertEqual(0.1, timestep.reward)
    self.assertTrue(timestep.mid())
    self.assertEqual({'a': 123}, gym_env.step_info())

    self.assertEqual(image, gym_env.render())


if __name__ == '__main__':
  absltest.main()
