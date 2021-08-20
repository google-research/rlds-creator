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

"""Tests for the environment proxy."""

from absl.testing import absltest
import gym
from rlds_creator import environment
from rlds_creator import environment_proxy
from rlds_creator import study_pb2
from rlds_creator.envs import procgen_env


def create_env_fn(
    env_spec: study_pb2.EnvironmentSpec) -> environment.Environment:
  return procgen_env.ProcgenEnvironment(env_spec)


class EnvironmentProxyTest(absltest.TestCase):

  def test_create(self):
    env_id = 'coinrun'
    env = environment_proxy.create_proxied_env_from_spec(
        study_pb2.EnvironmentSpec(
            procgen=study_pb2.EnvironmentSpec.Procgen(id=env_id)),
        create_env_fn)
    dm_env = env.env()
    timestep = dm_env.reset()
    self.assertTrue(timestep.first())

    # environment.Environment methods.
    metadata = env.metadata()
    self.assertEqual(env_id, metadata['env_name'])

    self.assertEqual(env.keys_to_action({'Up': 1}), 5)
    self.assertEqual(
        env.user_input_to_action(environment.UserInput(keys={'Up': 1})), 5)

    image = env.render()
    self.assertEqual(image.shape, (512, 512, 3))

    # dm_env.Environment methods. Reset is checked above.
    self.assertEqual(dm_env.observation_spec().shape, (64, 64, 3))
    self.assertEqual(dm_env.action_spec().num_values, 15)

    timestep = dm_env.step(5)
    self.assertTrue(timestep.mid())

    # Check setting the camera.
    env.set_camera(1)

    dm_env.close()

  def test_create_failure(self):
    with self.assertRaises(
        gym.error.UnregisteredEnv,
        msg='No registered env with id: procgen-invalid-v0'):
      environment_proxy.create_proxied_env_from_spec(
          study_pb2.EnvironmentSpec(
              procgen=study_pb2.EnvironmentSpec.Procgen(id='invalid')),
          create_env_fn)


if __name__ == '__main__':
  absltest.main()
