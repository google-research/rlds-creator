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

"""Tests for rlds_creator.procgen."""

from absl.testing import absltest
from rlds_creator import study_pb2
from rlds_creator.envs import procgen_env

ProcgenSpec = study_pb2.EnvironmentSpec.Procgen


class ProcgenTest(absltest.TestCase):

  def test_create(self):
    env = procgen_env.ProcgenEnvironment(
        study_pb2.EnvironmentSpec(
            max_episode_steps=500,
            procgen=ProcgenSpec(
                id='coinrun',
                distribution_mode=ProcgenSpec.DISTRIBUTION_HARD,
                num_levels=10,
                start_level=5,
                use_sequential_levels=True)))

    metadata = env.metadata()
    self.assertDictEqual(
        dict(
            metadata,
            distribution_mode=1,
            env_name='coinrun',
            num_actions=15,
            num_levels=10,
            start_level=5,
            use_sequential_levels=True), metadata)
    self.assertContainsSubset({'rand_seed'}, metadata)

    dm_env = env.env()
    self.assertEqual(dm_env.observation_spec().shape, (64, 64, 3))
    self.assertEqual(dm_env.action_spec().num_values, 15)

    key_mapping = [
        ({
            'Left': 1
        }, 1),
        ({
            'Right': 1
        }, 7),
        ({
            'Up': 1
        }, 5),
        ({
            'Down': 1
        }, 3),
        ({
            ' ': 1
        }, 4),  # Space bar is not used in this game.
        ({}, 4),  # No keys
        # Gamepad inputs.
        ({
            'Button12': 1
        }, 5),
        ({
            'Button15': 1
        }, 7),
        ({
            'Button13': 1
        }, 3),
        ({
            'Button14': 1
        }, 1),
        ({
            'Button0': 1  # Action key.
        }, 9),
    ]
    for keys, action in key_mapping:
      self.assertEqual(env.keys_to_action(keys), action)

    dm_env.reset()
    image = env.render()
    self.assertEqual(image.shape, (512, 512, 3))

    # Check that step information is present.
    dm_env.step(4)
    self.assertIn('level_complete', env.step_info())


if __name__ == '__main__':
  absltest.main()
