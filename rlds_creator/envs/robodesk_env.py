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

"""RoboDesk environments."""

from typing import Optional

import numpy as np
from rlds_creator import environment
from rlds_creator import gym_utils
from rlds_creator import input_utils
from rlds_creator import study_pb2
from robodesk import robodesk


# Width and height of the camera. This is not used for the image observations.
# It should be smaller than the size of the offscreen buffer.
CAMERA_SIZE = 480

RoboDeskSpec = study_pb2.EnvironmentSpec.RoboDesk

# Mapping from reward enums to the string representations.
_REWARD = {
    RoboDeskSpec.REWARD_DENSE: 'dense',
    RoboDeskSpec.REWARD_SPARSE: 'sparse',
    RoboDeskSpec.REWARD_SUCCESS: 'success',
}

# Mapping from actions to the corresponding keys.
_ACTION_MAPPING = [
    (np.array([-1., 0, 0, 0, 0]), ['a', 'Left']),
    (np.array([+1., 0, 0, 0, 0]), ['d', 'Right', 'Axis0']),
    (np.array([0, +1., 0, 0, 0]), ['w', 'Up']),
    (np.array([0, -1., 0, 0, 0]), ['s', 'Down', 'Axis1']),
    (np.array([0, 0, +1., 0, 0]), ['r', 'Button6']),
    (np.array([0, 0, -1., 0, 0]), ['f', 'Button7']),
    # Rotates the hand.
    (np.array([0, 0, 0, +1., 0]), ['q', 'Button4']),
    (np.array([0, 0, 0, -1., 0]), ['e', 'Button5']),
    # Opens and closes the gripper.
    (np.array([0, 0, 0, 0, +1.]), ['t', 'Button2']),
    (np.array([0, 0, 0, 0, -1.]), ['g', 'Button1']),
]

# Mapping from keys to the actions.
_KEY_MAPPING = {key: action for action, keys in _ACTION_MAPPING for key in keys}

# Default camera is (mostly) top-view and is the original setting in RoboDesk.
_CAMERAS = [
    ('default', {
        'distance': 1.8,
        'azimuth': 90,
        'elevation': -60
    }),
    ('sideview', {
        'distance': 1.8,
        'azimuth': 0,
        'elevation': -60
    }),
]

from dm_control import mujoco
from PIL import Image


class RoboDesk(robodesk.RoboDesk):
  """RoboDesk environment with parametric rendering."""

  def render(self, mode='rgb_array', resize=True, params=None):
    if params is None:
      params = {'size': 120, 'crop_box': (16.75, 25.0, 105.0, 88.75)}
      params.update(_CAMERAS[0][1])

    camera = mujoco.Camera(
        physics=self.physics,
        height=params['size'],
        width=params['size'],
        camera_id=-1)
    camera._render_camera.distance = params['distance']
    camera._render_camera.azimuth = params['azimuth']
    camera._render_camera.elevation = params['elevation']
    camera._render_camera.lookat[:] = [0, 0.535, 1.1]

    image = camera.render(depth=False, segmentation=False)
    camera._scene.free()

    if resize:
      image = Image.fromarray(image).crop(box=params['crop_box'])
      image = image.resize([self.image_size, self.image_size],
                           resample=Image.ANTIALIAS)
      image = np.asarray(image)
    return image


class RoboDeskEnvironment(gym_utils.GymEnvironment):
  """A RoboDesk environment."""

  def __init__(self, env_spec: study_pb2.EnvironmentSpec):
    args = env_spec.robodesk
    reward = _REWARD.get(args.reward)
    if not reward:
      raise ValueError('Unsupported reward type.')

    gym_env = RoboDesk(
        task=args.task,
        reward=reward,
        action_repeat=args.action_repeat,
        episode_length=env_spec.max_episode_steps,
        image_size=args.image_size)
    # Use the default camera.
    self.set_camera(0)

    super().__init__(gym_env)

  def keys_to_action(self, keys: environment.Keys) -> np.ndarray:
    keys = input_utils.get_mapped_keys(keys, input_utils.DEFAULT_BUTTON_MAPPING)
    action = np.zeros(5)
    for key, value in keys.items():
      if key in _KEY_MAPPING:
        action += _KEY_MAPPING[key] * value
    return action

  def render(self) -> environment.Image:
    # We use a larger image size and camera specific rendering parameters.
    # Cropping, which is enabled by resize, is also disabled.
    params = {'size': CAMERA_SIZE}
    params.update(self._render_params)
    return self._renderer.render(params=params, resize=False)

  def set_camera(self, index: int) -> Optional[environment.Camera]:
    if index >= len(_CAMERAS):
      return None
    name, self._render_params = _CAMERAS[index]
    return environment.Camera(index=index, name=name)
