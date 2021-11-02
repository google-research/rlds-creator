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

"""Robosuite environments."""

from typing import Dict, Optional

import dm_env
from dm_env import specs
import numpy as np
from rlds_creator import camera_observation_wrapper
from rlds_creator import environment
from rlds_creator import input_utils
from rlds_creator import study_pb2
import robosuite
from robosuite.environments import base
from robosuite.utils import input_utils as robosuite_input_utils
from robosuite.utils import macros
from robosuite.utils import transform_utils
from robosuite.wrappers import visualization_wrapper

# Do not concatenate images. This slows down the rendering and camera
# observations significantly.
macros.CONCATENATE_IMAGES = False
# With opengl convention, the images will be inverted.
macros.IMAGE_CONVENTION = 'opencv'

# Width and height of the camera; render() method will return images with these
# sizes.
CAMERA_WIDTH = 256
CAMERA_HEIGHT = 256

# Default maximum number of steps in an episode.
DEFAULT_HORIZON = 1000

# Gripper.
_KEY_MAPPING = {'Button0': ' '}


class DMEnvWrapper(dm_env.Environment):
  """Converts a Robosuite environment to a DM environment."""

  def __init__(self, env):
    self._env = env
    self._reset_required = True

  def reset(self) -> dm_env.TimeStep:
    self._reset_required = False
    return dm_env.restart(self._env.reset())

  def step(self, action) -> dm_env.TimeStep:
    if self._reset_required:
      return self.reset()
    observation, reward, done, _ = self._env.step(action)
    self._reset_required = done
    return (dm_env.termination(reward, observation)
            if done else dm_env.transition(reward, observation))

  def observation_spec(self) -> Dict[str, specs.Array]:
    spec = {}
    for name, obs in self._env.observation_spec().items():
      # Items of the observation specs are sample observations. We create the
      # spec based on their properties.
      arr = np.array(obs)
      spec[name] = specs.Array(shape=arr.shape, dtype=arr.dtype, name=name)
    return spec

  def action_spec(self) -> specs.BoundedArray:
    minimum, maximum = self._env.action_spec
    return specs.BoundedArray(
        shape=minimum.shape,
        dtype=minimum.dtype,
        minimum=minimum,
        maximum=maximum)

  def close(self):
    self._env.close()


class _CameraObsWrapper(camera_observation_wrapper.CameraObservationWrapper):
  """Camera observation wrapper for a Robosuite environment."""

  def __init__(self, env: dm_env.Environment, robosuite_env: base.MujocoEnv,
               camera: str):
    self._robosuite_env = robosuite_env
    super().__init__(env, camera)

  def _render(self, camera: str) -> environment.Image:
    """Returns the environment as an image."""
    image = self._robosuite_env.sim.render(
        height=CAMERA_HEIGHT, width=CAMERA_WIDTH, camera_name=camera)
    # With opencv image convention the images in the observations will have the
    # correct orientation, but not the image that is rendered from the
    # similation. We invert it.
    return image[::-1]


# This is a modified version of Keyboard class in
# third_party/py/robosuite/devices/keyboard.py. Due to (missing) dependencies,
# it is not possible to use it directly.
class Keyboard(object):
  """Keyboard device."""

  def __init__(self, pos_sensitivity=1.0, rot_sensitivity=1.0):
    """Creates a keyboard device.

    Args:
      pos_sensitivity (float): Magnitude of input position command scaling.
      rot_sensitivity (float): Magnitude of scale input rotation commands
        scaling.
    """
    self._reset_internal_state()

    self._reset_state = 0
    # In Robosuite v1.2, the gains have changed. We use higher step values to
    # compensate for this this and have action vectors that are similar to the
    # existing ones.
    self._pos_step = 0.4 / 5
    self._rot_step = 0.075
    # The analog inputs are more sensitive with high gain, so we use a small
    # multiplier.
    self._analog_input_coeff = 0.1

    self.pos_sensitivity = pos_sensitivity
    self.rot_sensitivity = rot_sensitivity

  def _reset_internal_state(self):
    """Resets internal state of controller, except for the reset signal."""
    self.rotation = np.array([[-1., 0., 0.], [0., 1., 0.], [0., 0., -1.]])
    self.raw_drotation = np.zeros(
        3)  # immediate roll, pitch, yaw delta values from keyboard hits
    self.last_drotation = np.zeros(3)
    self.pos = np.zeros(3)  # (x, y, z)
    self.last_pos = np.zeros(3)
    self.grasp = False
    self.last_keys = []

  def start_control(self):
    self._reset_internal_state()
    self._reset_state = 0

  def get_controller_state(self):
    """Grabs the current state of the keyboard.

    Returns:
      dict: A dictionary containing dpos, orn, unmodified orn, grasp, and reset
    """
    dpos = self.pos - self.last_pos
    self.last_pos = np.array(self.pos)
    raw_drotation = self.raw_drotation - self.last_drotation
    self.last_drotation = np.array(self.raw_drotation)
    return dict(
        dpos=dpos,
        rotation=self.rotation,
        raw_drotation=raw_drotation,
        grasp=int(self.grasp),
        reset=self._reset_state,
    )

  def _update_pos(self, axis: int, value: float):
    """Updates the position value of the specified axis."""
    self.pos[axis] += self._pos_step * self.pos_sensitivity * value

  # Direction vectors for the axes. x<->y axes are switched.
  _DIRECTIONS = [[0., 1., 0.], [1., 0., 0.], [0., 0., 1.]]

  def _update_rot(self, axis: int, value: float):
    """Updates the rotation value of the specified axis."""
    value *= self._rot_step * self.rot_sensitivity
    drot = transform_utils.rotation_matrix(
        angle=value, direction=self._DIRECTIONS[axis])[:3, :3]
    self.rotation = self.rotation.dot(drot)  # rotates x
    self.raw_drotation[axis] += value

  def on_press(self, key: str, value: float, is_spacemouse: bool):
    """Key handler for key presses."""
    is_analog = key.startswith('Axis') or key in ['Button6', 'Button7']
    if is_analog:
      value *= self._analog_input_coeff
    # Controls for moving position
    if key == 'w':
      self._update_pos(0, -1.0)  # dec x
    elif key == 's':
      self._update_pos(0, +1.0)  # inc x
    elif key == 'Axis1':
      self._update_pos(0, value)  # x
    elif key == 'a':
      self._update_pos(1, -1.0)  # dec y
    elif key == 'd':
      self._update_pos(1, +1.0)  # inc y
    elif key == 'Axis0':
      self._update_pos(1, value)  # y
    elif key == 'f':
      self._update_pos(2, -1.0)  # dec z
    elif key == 'Button7':
      self._update_pos(2, -value)
    elif key == 'r':
      self._update_pos(2, +1.0)  # inc z
    elif key == 'Button6':
      self._update_pos(2, value)
    elif is_spacemouse and key == 'Axis2':
      self._update_pos(2, -value)  # z

    # Controls for moving orientation
    elif key == 'z':
      self._update_rot(1, +1.0)  # rotates x
    elif key == 'x':
      self._update_rot(1, -1.0)
    elif key == 'Axis2' and not is_spacemouse:
      self._update_rot(1, -value)
    elif key == 'Axis4' and is_spacemouse:
      self._update_rot(1, value)
    elif key == 't':
      self._update_rot(0, +1.0)  # rotates y
    elif key == 'g':
      self._update_rot(0, -1.0)
    elif key == 'Axis3':
      self._update_rot(0, value)
    elif key == 'c' or key == 'Button4':
      self._update_rot(2, +1.0)  # rotates z
    elif key == 'v' or key == 'Button5':
      self._update_rot(2, -1.0)
    elif key == 'Axis5' and is_spacemouse:
      self._update_rot(2, value)

  def process_keys(self, keys: environment.Keys, is_spacemouse: bool):
    for key, value in keys.items():
      self.on_press(key, value, is_spacemouse)
    # Grasping works like a toggle.
    if ' ' in keys and ' ' not in self.last_keys:
      self.grasp = not self.grasp
    self.last_keys = keys


class RobosuiteEnvironment(environment.Environment):
  """An Robosuite environment."""

  def __init__(self, env_spec: study_pb2.EnvironmentSpec):
    args = env_spec.robosuite
    self._args = args
    self._cameras = list(args.cameras)
    # Fallback to agentview if there is no camera specified.
    if not self._cameras:
      self._cameras = ['agentview']
    # The initialization steps below are based on
    # third_party/py/robosuite/scripts/collect_human_demonstrations.py.
    controller_config = robosuite.load_controller_config(
        default_controller=args.controller)
    config = {
        'camera_heights': CAMERA_HEIGHT,
        'camera_names': self._cameras,
        'camera_widths': CAMERA_WIDTH,
        'controller_configs': controller_config,
        'control_freq': 20,
        'env_name': args.id,
        'horizon': env_spec.max_episode_steps or DEFAULT_HORIZON,
        'reward_shaping': True,
        'robots': list(args.robots),
        'use_camera_obs': args.use_camera_obs,
    }
    # Check if we're using a multi-armed environment and use env_configuration
    # argument if so.
    if 'TwoArm' in args.id:
      config['env_configuration'] = args.config

    # Environment metadata.
    self._metadata = {
        'pos_sensitivity': args.pos_sensitivity,
        'rot_sensitivity': args.rot_sensitivity
    }
    self._metadata.update(config)

    self._robosuite_env = robosuite.make(
        **config,
        hard_reset=False,
        # Offscreen renderer and rendered are mutually exclusive. We use the
        # offscreen one.
        has_offscreen_renderer=True,
        has_renderer=False,
        # Terminate after horizon steps.
        ignore_done=False)
    self._env = _CameraObsWrapper(
        DMEnvWrapper(
            visualization_wrapper.VisualizationWrapper(self._robosuite_env)),
        self._robosuite_env, self._cameras[0])
    self._keyboard = Keyboard(
        pos_sensitivity=args.pos_sensitivity,
        rot_sensitivity=args.rot_sensitivity)
    self._keyboard.start_control()
    # Index of the active robot.
    self._active_robot = int(args.arm == 'left' and args.config != 'bimanual')

  def env(self) -> environment.DMEnv:
    """Returns the DM environment."""
    return self._env

  def keys_to_action(self, keys: environment.Keys):
    """Maps the pressed keys to an action in the environment."""
    return self.user_input_to_action(environment.UserInput(keys=keys))

  def user_input_to_action(self, user_input: environment.UserInput):
    """Maps the user input to an action in the environment."""
    is_spacemouse = user_input.controller == environment.Controller.SPACEMOUSE
    keys = input_utils.get_mapped_keys(user_input.keys, _KEY_MAPPING)
    # We have a custom handling of the gamepad input and do not use the standard
    # mapping.
    self._keyboard.process_keys(keys, is_spacemouse)
    action, _ = robosuite_input_utils.input2action(
        device=self._keyboard,
        robot=self._robosuite_env.robots[self._active_robot],
        active_arm=self._args.arm,
        env_configuration=self._args.config)
    return action

  def render(self) -> environment.Image:
    """Returns the environment as an image."""
    return self._env.render()

  def set_camera(self, index: int) -> Optional[environment.Camera]:
    """Sets the camera to render images."""
    if index < 0 or index >= len(self._cameras):
      return None
    camera = self._cameras[index]
    self._env.set_camera(camera)
    return environment.Camera(index=index, name=camera)

  def metadata(self) -> environment.Metadata:
    """Returns the metadata about the environment."""
    return self._metadata
