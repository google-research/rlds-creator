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

"""Tests for the Atari environment."""

from absl.testing import absltest
from rlds_creator import study_pb2
from rlds_creator.envs import atari_env


class AtariTest(absltest.TestCase):

  def test_create(self):
    env = atari_env.AtariEnvironment(
        study_pb2.EnvironmentSpec(
            atari=study_pb2.EnvironmentSpec.Atari(
                id='MontezumaRevenge', sticky_actions=True)))

    dm_env = env.env()
    self.assertEqual(dm_env.observation_spec().shape, (210, 160, 3))
    self.assertEqual(dm_env.action_spec().num_values, 18)

    key_mapping = [
        ({
            'Left': 1
        }, 4),
        ({
            'Right': 1
        }, 3),
        ({
            'Up': 1
        }, 2),
        ({
            'Down': 1
        }, 5),
        ({
            ' ': 1
        }, 1),
        ({}, 0),  # No keys
        # Gamepad inputs.
        ({
            'Button12': 1
        }, 2),
        ({
            'Button15': 1
        }, 3),
        ({
            'Button13': 1
        }, 5),
        ({
            'Button14': 1
        }, 4)
    ]
    for keys, action in key_mapping:
      self.assertEqual(env.keys_to_action(keys), action)

    dm_env.reset()
    image = env.render()
    self.assertEqual(image.shape, (210, 160, 3))

    # Check that step information is present.
    dm_env.step(1)
    self.assertIn('ale.lives', env.step_info())


if __name__ == '__main__':
  absltest.main()
