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

"""Episode storage that uses Riegeli files."""

from typing import Any, Optional, Sequence

import envlogger
from envlogger.backends import riegeli_backend_writer
from envlogger.converters import spec_codec
from rlds_creator import environment
from rlds_creator import episode_storage
from rlds_creator import file_utils


class RiegeliEpisodeReader(episode_storage.EpisodeReader):
  """Episode reader for the Riegeli writer.

  This is the format used by the envlogger. See pypi.org/project/envlogger.
  """

  def __init__(self, tag_directory: str, index: int = 0):
    """Creates a RiegeliEpisodeReader.

    Args:
      tag_directory: Path of the tag directory.
      index: Index of the episode in the dataset.
    """
    self._reader = envlogger.Reader(tag_directory)
    self._steps = self._reader.episodes[index]
    self._metadata = self._reader.episode_metadata()[index]

  @property
  def metadata(self) -> episode_storage.EpisodeMetadata:
    return self._metadata

  @property
  def steps(self) -> Sequence[envlogger.StepData]:
    return self._steps

  def action_spec(self) -> Any:
    return self._reader.action_spec()

  def discount_spec(self) -> Any:
    return self._reader.discount_spec()

  def observation_spec(self) -> Any:
    return self._reader.observation_spec()

  def reward_spec(self) -> Any:
    return self._reader.reward_spec()


class RiegeliEpisodeWriter(episode_storage.EpisodeWriter):
  """Episode writer that stores data as Riegeli files.

  This is the format used by the envlogger. See pypi.org/project/envlogger.
  """

  def __init__(self,
               env: environment.DMEnv,
               tag_directory: str,
               metadata: Optional[episode_storage.EnvironmentMetadata] = None):
    """Creates a RiegeliEpisodeWriter.

    Args:
      env: a DM environment used to record the episodes.
      tag_directory: Path of the tag directory to store dataset.
      metadata: Metadata of the environment.
    """
    super().__init__()
    # Make sure that the directory exists.
    file_utils.make_dirs(tag_directory)
    self._tag_directory = tag_directory
    self._index = 0
    backend_metadata = {
        'environment_specs': spec_codec.encode_environment_specs(env)
    }
    if metadata:
      backend_metadata.update(metadata)
    self._backend = riegeli_backend_writer.RiegeliBackendWriter(
        tag_directory, metadata=backend_metadata)
    self._is_new_episode = True

  def start_episode(self):
    self._is_new_episode = True

  def record_step(self, data: episode_storage.StepData):
    self._backend.record_step(envlogger.StepData(*data), self._is_new_episode)
    self._is_new_episode = False

  def end_episode(
      self,
      metadata: Optional[episode_storage.EpisodeMetadata] = None
  ) -> episode_storage.EpisodeStorageSpec:
    if metadata:
      # Episode metadata will be written on the next call to record_step() or
      # when the writer is closed.
      self._backend.set_episode_metadata(metadata)
    self._is_new_episode = True
    spec = episode_storage.EpisodeStorageSpec(
        environment_logger=episode_storage.EpisodeStorageSpec.EnvironmentLogger(
            tag_directory=self._tag_directory, index=self._index))
    # Increment the episode index.
    self._index += 1
    return spec

  def _close(self):
    self._backend.close()
