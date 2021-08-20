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

"""Tests for the Robosuite environment."""

from absl.testing import absltest
import numpy as np
import numpy.testing as npt
from rlds_creator import environment
from rlds_creator import study_pb2
from rlds_creator.envs import robosuite_env


class RobosuiteTest(absltest.TestCase):

  def test_create(self):
    env = robosuite_env.RobosuiteEnvironment(
        study_pb2.EnvironmentSpec(
            robosuite=study_pb2.EnvironmentSpec.Robosuite(
                id='Lift', robots=['Panda'], config='single-arm-opposed')))

    self.assertDictEqual(
        env.metadata(), {
            'camera_heights': 256,
            'camera_names': ['agentview'],
            'camera_widths': 256,
            'control_freq': 20,
            'controller_configs': {
                'type': 'OSC_POSE',
                'input_max': 1,
                'input_min': -1,
                'output_max': [0.05, 0.05, 0.05, 0.5, 0.5, 0.5],
                'output_min': [-0.05, -0.05, -0.05, -0.5, -0.5, -0.5],
                'kp': 150,
                'damping_ratio': 1,
                'impedance_mode': 'fixed',
                'kp_limits': [0, 300],
                'damping_ratio_limits': [0, 10],
                'position_limits': None,
                'orientation_limits': None,
                'uncouple_pos_ori': True,
                'control_delta': True,
                'interpolation': None,
                'ramp_ratio': 0.2
            },
            'env_name': 'Lift',
            'horizon': 1000,
            'pos_sensitivity': 1.5,
            'reward_shaping': True,
            'robots': ['Panda'],
            'rot_sensitivity': 1.5,
            'use_camera_obs': False,
        })

    dm_env = env.env()
    # Robosuite observation is a dictionary.
    self.assertSetEqual(
        set(dm_env.observation_spec().keys()), {
            'robot0_joint_pos_cos', 'robot0_joint_pos_sin', 'robot0_joint_vel',
            'robot0_eef_pos', 'robot0_eef_quat', 'robot0_gripper_qpos',
            'robot0_gripper_qvel', 'robot0_proprio-state', 'cube_pos',
            'cube_quat', 'gripper_to_cube_pos', 'object-state'
        })
    self.assertEqual(dm_env.action_spec().shape, (7,))

    # Mapping from the keys to the action vectors.
    actions = {
        'w': [-15., 0., 0., 0., 0., 0., -1.],
        's': [15., 0., 0., 0., 0., 0., -1.],
        'a': [0., -15., 0., 0., 0., 0., -1.],
        'd': [0., 15., 0., 0., 0., 0., -1.],
        'f': [0., 0., -15., 0., 0., 0., -1.],
        'r': [0., 0., 15., 0., 0., 0., -1.],
        'z': [0., 0., 0., 5.625, 0., 0., -1.],
        'x': [0., 0., 0., -5.625, 0., 0., -1.],
        't': [0., 0., 0., 0., 5.625, 0., -1.],
        'g': [0., 0., 0., 0., -5.625, 0., -1.],
        'c': [0., 0., 0., 0., 0., -5.625, -1.],
        'Button4': [0., 0., 0., 0., 0., -5.625, -1.],
        'v': [0., 0., 0., 0., 0., 5.625, -1.],
        'Button5': [0., 0., 0., 0., 0., 5.625, -1.],
    }

    for key, action in actions.items():
      npt.assert_allclose(env.keys_to_action({key: 1}), action, atol=0.01)

    analog_actions = {
        ('Axis0', -1.0): [0., -1.5, 0., 0., 0., 0., -1.],
        ('Axis0', -0.5): [0., -0.75, 0., 0., 0., 0., -1.],
        ('Axis0', 0.5): [0., 0.75, 0., 0., 0., 0., -1.],
        ('Axis0', 1.0): [0., 1.5, 0., 0., 0., 0., -1.],
        ('Axis1', -1.0): [-1.5, 0., 0., 0., 0., 0., -1.],
        ('Axis1', -0.5): [-0.75, 0., 0., 0., 0., 0., -1.],
        ('Axis1', 0.5): [0.75, 0., 0., 0., 0., 0., -1.],
        ('Axis1', 1.0): [1.5, 0., 0., 0., 0., 0., -1.],
        ('Axis2', -1.0): [0., 0., 0., 0.5625, 0., 0., -1.],
        ('Axis2', -0.5): [0., 0., 0., 0.28125, 0., 0., -1.],
        ('Axis2', 0.5): [0., 0., 0., -0.28125, 0., 0., -1.],
        ('Axis2', 1.0): [0., 0., 0., -0.5625, 0., 0., -1.],
        ('Axis3', -1.0): [0., 0., 0., 0., -0.5625, 0., -1.],
        ('Axis3', -0.5): [0., 0., 0., 0., -0.28125, 0., -1.],
        ('Axis3', 0.5): [0., 0., 0., 0., 0.28125, 0., -1.],
        ('Axis3', 1.0): [0., 0., 0., 0., 0.5625, 0., -1.],
    }

    for (key, value), action in analog_actions.items():
      npt.assert_allclose(env.keys_to_action({key: value}), action, atol=0.01)

    spacemouse_actions = {
        # Direction.
        ('Axis0', -1.0): [0., -1.5, 0., 0., 0., 0., -1.],
        ('Axis0', 1.0): [0., 1.5, 0., 0., 0., 0., -1.],
        ('Axis1', -1.0): [-1.5, 0., 0., 0., 0., 0., -1.],
        ('Axis1', 1.0): [1.5, 0., 0., 0., 0., 0., -1.],
        ('Axis2', -1.0): [0, 0., 1.5, 0., 0., 0., -1.],
        ('Axis2', 1.0): [0, 0., -1.5, 0., 0., 0., -1.],
        # Rotation.
        ('Axis3', -1.0): [0., 0., 0., 0., -0.5625, 0., -1.],
        ('Axis3', 1.0): [0., 0., 0., 0., 0.5625, 0., -1.],
        ('Axis4', -1.0): [0., 0., 0., -0.5625, 0., 0., -1.],
        ('Axis4', 1.0): [0., 0., 0., 0.5625, 0., 0., -1.],
        ('Axis5', -1.0): [0., 0., 0., 0., 0., 0.5625, -1.],
        ('Axis5', 1.0): [0., 0., 0., 0., 0., -0.5625, -1.],
    }

    for (key, value), action in spacemouse_actions.items():
      npt.assert_allclose(
          env.user_input_to_action(
              environment.UserInput(
                  keys={key: value},
                  controller=environment.Controller.SPACEMOUSE)),
          action,
          atol=0.01)

    dm_env.reset()
    image = env.render()
    self.assertEqual(image.shape, (256, 256, 3))

  def test_use_camera_obs(self):
    env = robosuite_env.RobosuiteEnvironment(
        study_pb2.EnvironmentSpec(
            robosuite=study_pb2.EnvironmentSpec.Robosuite(
                id='Lift',
                robots=['Panda'],
                config='single-arm-opposed',
                use_camera_obs=True,
                cameras=['agentview', 'frontview'])))

    dm_env = env.env()
    self.assertIn('agentview_image', dm_env.observation_spec().keys())
    self.assertIn('frontview_image', dm_env.observation_spec().keys())

    timestep = dm_env.reset()
    camera_obs = timestep.observation['agentview_image']
    self.assertEqual((256, 256, 3), camera_obs.shape)
    image = env.render()
    # Observation and rendered image should be the same.
    npt.assert_equal(camera_obs, image)

    # Change the camera.
    camera_obs = timestep.observation['frontview_image']
    self.assertEqual((256, 256, 3), camera_obs.shape)
    camera = env.set_camera(1)
    self.assertEqual(environment.Camera(1, 'frontview'), camera)
    image = env.render()
    npt.assert_equal(camera_obs, image)
    # Reset the image from observation to check that the inversion happens.
    env._env._image = None
    image = env.render()
    # Rendering may not be deterministic, e.g. due to texture mapping. We allow
    # small divergence less than 1%.
    self.assertLess(
        np.count_nonzero(image != camera_obs) / np.array(image).size, 0.01)

    # Third camera is not present.
    self.assertIsNone(env.set_camera(2))

  def test_max_episode_steps(self):
    max_episode_steps = 10
    env = robosuite_env.RobosuiteEnvironment(
        study_pb2.EnvironmentSpec(
            max_episode_steps=max_episode_steps,
            robosuite=study_pb2.EnvironmentSpec.Robosuite(
                id='Lift', robots=['Panda'], config='single-arm-opposed')))

    dm_env = env.env()
    timestep = dm_env.reset()
    steps = 0
    while not timestep.last():
      timestep = dm_env.step(env.keys_to_action({'W': 1}))
      steps += 1

    self.assertEqual(max_episode_steps, steps)


if __name__ == '__main__':
  absltest.main()
