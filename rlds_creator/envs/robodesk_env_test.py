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

"""Tests for robodesk_env."""

from absl.testing import absltest
from rlds_creator import environment
from rlds_creator import study_pb2
from rlds_creator.envs import robodesk_env

RoboDeskSpec = study_pb2.EnvironmentSpec.RoboDesk


class RobodeskEnvTest(absltest.TestCase):

  def test_create(self):
    env = robodesk_env.RoboDeskEnvironment(
        study_pb2.EnvironmentSpec(
            max_episode_steps=500,
            robodesk=RoboDeskSpec(
                task='open_slide',
                reward=RoboDeskSpec.REWARD_DENSE,
                action_repeat=2,
                image_size=32)))

    dm_env = env.env()
    # RoboDesk observation is a dictionary.
    self.assertSetEqual(
        set(dm_env.observation_spec().keys()), {
            'image', 'qpos_robot', 'qvel_robot', 'end_effector', 'qpos_objects',
            'qvel_objects'
        })
    self.assertEqual(dm_env.action_spec().shape, (5,))

    # TODO(sertan): Check actions.

    dm_env.reset()
    image = env.render()
    self.assertEqual(image.shape, (480, 480, 3))

    # Check setting the cameras and rendering through them.
    for index, name in enumerate(['default', 'sideview']):
      self.assertEqual(
          environment.Camera(name=name, index=index), env.set_camera(index))
      env.render()

    self.assertIsNone(env.set_camera(2))


if __name__ == '__main__':
  absltest.main()
