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

"""Episode storage that uses Pickle files."""

import os
import pickle
from typing import Any, Optional, Sequence

from rlds_creator import environment
from rlds_creator import episode_storage
from rlds_creator import file_utils


class PickleEpisodeReader(episode_storage.EpisodeReader):
  """Episode reader for the Pickle writer."""

  def __init__(self, path: str):
    """Creates a PickleEpisodeReader.

    Args:
      path: Path of the Pickle file.
    """
    # Episode metadata will be stored as a dictionary.
    with file_utils.open_file(path, 'rb') as f:
      self._data = pickle.load(f)

  @property
  def metadata(self) -> episode_storage.EpisodeMetadata:
    return self._data['metadata']

  @property
  def steps(self) -> Sequence[episode_storage.StepData]:
    return self._data['steps']

  def action_spec(self) -> Any:
    return self._data['action_spec']

  def discount_spec(self) -> Any:
    return self._data['discount_spec']

  def observation_spec(self) -> Any:
    return self._data['observation_spec']

  def reward_spec(self) -> Any:
    return self._data['reward_spec']


class PickleEpisodeWriter(episode_storage.EpisodeWriter):
  """Episode writer that stores episode data as Pickle files.

  The data of each episode will be stored as a separate Pickle file under a base
  directory. The name of the file will be of the form [episode index].pkl and it
  will contain a dictionary with metadata, steps, {action, discount,
  observation, reward}_spec fields.
  """

  def __init__(self,
               env: environment.DMEnv,
               base_dir: str,
               metadata: Optional[episode_storage.EnvironmentMetadata] = None):
    """Creates a PickleEpisodeWriter.

    Args:
      env: a DM environment used to record the episodes.
      base_dir: Path of the directory to store the Pickle files.
      metadata: Metadata of the environment.
    """
    super().__init__()
    self._env = env
    self._base_dir = base_dir
    # Make sure that the base directory exists.
    file_utils.make_dirs(base_dir)
    # Index of an episode. This will also be used as the name of the Pickle file
    # with .pkl extension.
    self._index = 0
    # Steps of the current episode.
    self._steps = []

  def start_episode(self):
    self._steps = []

  def record_step(self, data: episode_storage.StepData):
    self._steps.append(data)

  def end_episode(
      self,
      metadata: Optional[episode_storage.EpisodeMetadata] = None
  ) -> episode_storage.EpisodeStorageSpec:
    # Data of an episode is stored as a dictionary.
    data = {
        'metadata': metadata,
        'steps': self._steps,
        'action_spec': self._env.action_spec(),
        'discount_spec': self._env.discount_spec(),
        'observation_spec': self._env.observation_spec(),
        'reward_spec': self._env.reward_spec(),
    }
    filename = str(self._index) + '.pkl'
    path = os.path.join(self._base_dir, filename)
    with file_utils.open_file(path, 'wb') as f:
      pickle.dump(data, f)
    spec = episode_storage.EpisodeStorageSpec(
        pickle=episode_storage.EpisodeStorageSpec.Pickle(path=path))
    # Increment the episode index and reset the steps.
    self._index += 1
    self._steps = []
    return spec

  def _close(self):
    # Nothing to do.
    pass
