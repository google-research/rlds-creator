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

"""Storage for episode data."""

import abc
from typing import Any, Dict, NamedTuple, Optional, Sequence

from rlds_creator import environment
from rlds_creator import study_pb2

EpisodeStorageSpec = study_pb2.Episode.Storage
# Episode metadata may be arbitrary.
EpisodeMetadata = Any
# Environment metadata is a dictionary.
EnvironmentMetadata = Dict[str, Any]


# We use the same structure as the StepData in envlogger.
class StepData(NamedTuple):
  """Denotes a step of an episode."""
  # Timestep generated by the environment.
  timestep: environment.TimeStep
  # Action that led to the timestep.
  action: Any
  # Client-specific data for the step. This will also contain the internal data,
  # such as the rendered images and the user input.
  custom_data: Optional[Any] = None


class EpisodeReader(metaclass=abc.ABCMeta):
  """Interface for episodes readers.

  An episode reader provides access to the data for a single episode and the
  specifications of the environment used to record the episode.
  """

  @property
  @abc.abstractmethod
  def metadata(self) -> EpisodeMetadata:
    """Returns the metadata of the episode."""

  @property
  @abc.abstractmethod
  def steps(self) -> Sequence[StepData]:
    """Returns the steps of the episode."""

  @abc.abstractmethod
  def action_spec(self) -> Any:
    """Returns the action spec of the environment."""

  @abc.abstractmethod
  def discount_spec(self) -> Any:
    """Returns the discount spec of the environment."""

  @abc.abstractmethod
  def observation_spec(self) -> Any:
    """Returns the observation spec of the environment."""

  @abc.abstractmethod
  def reward_spec(self) -> Any:
    """Returns the reward spec of the environment."""


class EpisodeWriter(metaclass=abc.ABCMeta):
  """Interface for episode writers.

  An episode writer allows storing the data of one or several episodes. The
  typical usage for recording an episode is as follows:

  writer.start_episode()
  writer.record_step(StepData(environment.reset()))

  while not timestep.last():
    action = get_action(...)
    timestep = environment.step(action)
    writer.record_step(StepData(timestep, action))

  writer.end_episode(episode_metadata)
  """

  def __init__(self):
    self._closed = False

  @abc.abstractmethod
  def start_episode(self):
    """Starts a new episode."""

  @abc.abstractmethod
  def record_step(self, data: StepData):
    """Records the step data for the current episode."""

  @abc.abstractmethod
  def end_episode(self,
                  metadata: Optional[EpisodeMetadata] = None
                 ) -> EpisodeStorageSpec:
    """Ends the current episode and returns its spec.

    Args:
      metadata: Metadata for the episode.
    """

  def close(self):
    """Closes the episode writer."""
    self._close()
    self._closed = True

  @abc.abstractmethod
  def _close(self):
    """Called when the episode writer is closed."""

  def __del__(self):
    # Close the writer if needed.
    if not self._closed:
      self.close()


class EpisodeStorageFactory(metaclass=abc.ABCMeta):
  """Interface for episode storage factories."""

  @abc.abstractmethod
  def create_reader(self, spec: EpisodeStorageSpec) -> EpisodeReader:
    """Creates an episode reader.

    Args:
      spec: Specification of the episode storage.

    Returns:
      an EpisodeReader.
    """

  @abc.abstractmethod
  def create_writer(self,
                    kind: str,
                    env: environment.DMEnv,
                    *args,
                    metadata: Optional[EnvironmentMetadata] = None,
                    **kwargs) -> EpisodeWriter:
    """Creates an episode writer.

    Args:
      kind: Kind of the episode writer, e.g. pickle. See the comments in
        Episode.Storage message in study.proto for possible options.
      env: a DM environment that will be used to record the episodes.
      *args: Arguments passed to the writer.
      metadata: Metadata of the environment.
      **kwargs: Arguments passed to the writer.

    Returns:
      an EpisodeWriter.
    """
