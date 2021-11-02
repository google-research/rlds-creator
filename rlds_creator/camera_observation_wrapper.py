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

"""Wrapper that re-uses an image observation as rendering."""

import dm_env
from rlds_creator import environment
from rlds_creator import environment_wrapper


class CameraObservationWrapper(environment_wrapper.EnvironmentWrapper):
  """Environment wrapper that uses image observations as rendered image.

  Using the camera image in the observation dictionary avoid re-rendering the
  scene and avoid reduced frame rate. Sub-classes should implement the _render()
  method which explicitly renders an image if the image observation is not
  present.
  """

  def __init__(self, env: dm_env.Environment, camera: str):
    """Creates a CameraObservationWrapper.

    Args:
      env: Environment to be wrapped. Its observations should be a dictionary
        and contain images corresponding to the specified cameras.
      camera: Name of the camera.
    """
    super().__init__(env)
    self._image = None
    self._timestep = None
    self.set_camera(camera)

  def _maybe_update_image(self, timestep: dm_env.TimeStep) -> dm_env.TimeStep:
    """Updates the rendered image from the observation if available."""
    self._timestep = timestep
    if self._camera_observation_key in timestep.observation:
      self._image = timestep.observation[self._camera_observation_key]
    else:
      self._image = None
    return timestep

  def get_camera_observation_key(self, camera: str) -> str:
    """Returns the key in the observation dictionary for the camera."""
    return f'{camera}_image'

  def set_camera(self, camera: str):
    """Sets the camera to render."""
    self._camera = camera
    self._camera_observation_key = self.get_camera_observation_key(camera)
    if self._timestep:
      self._maybe_update_image(self._timestep)

  def step(self, action) -> dm_env.TimeStep:
    return self._maybe_update_image(self._environment.step(action))

  def reset(self) -> dm_env.TimeStep:
    return self._maybe_update_image(self._environment.reset())

  def _render(self, camera: str) -> environment.Image:
    """Renders the camera image.

    This method will be called if the image observation is not present.

    Args:
      camera: Name of the camera.

    Returns:
      a rendered image.
    """
    raise NotImplementedError()

  def render(self) -> environment.Image:
    """Returns the environment as an image."""
    # Use the image from the last observation if available; otherwise, render.
    if self._image is not None:
      return self._image
    return self._render(self._camera)
