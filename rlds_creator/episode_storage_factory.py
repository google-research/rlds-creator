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

"""Episode storage factory."""

from typing import Optional

from absl import logging
from rlds_creator import environment
from rlds_creator import episode_storage
from rlds_creator import pickle_episode_storage
from rlds_creator import riegeli_episode_storage


class EpisodeStorageFactory(episode_storage.EpisodeStorageFactory):
  """Episode storage factory."""

  def create_reader(
      self, spec: episode_storage.EpisodeStorageSpec
  ) -> episode_storage.EpisodeReader:
    logging.info('Creating reader for %r.', spec)
    kind = spec.WhichOneof('type')
    if kind == 'environment_logger':
      config = spec.environment_logger
      return riegeli_episode_storage.RiegeliEpisodeReader(
          config.tag_directory, config.index)
    if kind == 'pickle':
      return pickle_episode_storage.PickleEpisodeReader(spec.pickle.path)
    raise ValueError(f'Unsupported episode reader {kind}.')

  def create_writer(self,
                    kind: str,
                    env: environment.DMEnv,
                    *args,
                    metadata: Optional[
                        episode_storage.EnvironmentMetadata] = None,
                    **kwargs) -> episode_storage.EpisodeWriter:
    if kind == 'environment_logger':
      return riegeli_episode_storage.RiegeliEpisodeWriter(
          env, *args, metadata=metadata, **kwargs)
    if kind == 'pickle':
      return pickle_episode_storage.PickleEpisodeWriter(
          env, *args, metadata=metadata, **kwargs)
    raise ValueError(f'Unsupported episode writer {kind}.')
