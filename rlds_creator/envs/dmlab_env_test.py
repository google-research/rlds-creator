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

"""Tests for the DMLab environment."""

import os

from absl import flags
from absl.testing import absltest
import numpy.testing as npt
from rlds_creator import study_pb2
from rlds_creator.envs import dmlab_env
import deepmind_lab

flags.DEFINE_string('dmlab_homepath', None, 'Labyrinth homepath.')

FLAGS = flags.FLAGS


class DmlabTest(absltest.TestCase):

  def test_create(self):
    deepmind_lab.set_runfiles_path(FLAGS.dmlab_homepath)
    env = dmlab_env.DmLabEnvironment(
        study_pb2.EnvironmentSpec(
            dmlab=study_pb2.EnvironmentSpec.DMLab(
                id='explore_goal_locations_small')))

    dm_env = env.env()
    self.assertEqual(dm_env.observation_spec().shape, (256, 256, 3))
    self.assertEqual(dm_env.action_spec().shape, (7,))

    npt.assert_array_equal(
        env.keys_to_action({
            'Left': 1,
            'Up': 1,
            'Control': 1,
            ' ': 1
        }), [-20, -10, 0, 0, 1, 1, 0])

    # Gamepad.
    npt.assert_array_equal(
        env.keys_to_action({
            'Button14': 1,
            'Button12': 1,
            'Button1': 1,
            'Button3': 1
        }), [-20, -10, 0, 0, 1, 1, 0])

    npt.assert_array_equal(
        env.keys_to_action({
            'Axis0': -0.5,
            'Axis1': 0.5,
            'Axis2': -0.5,
            'Axis3': 0.5
        }), [-20, 10, -1, -1, 0, 0, 0])

    dm_env.reset()
    image = env.render()
    self.assertEqual(image.shape, (256, 256, 3))


if __name__ == '__main__':
  absltest.main()
