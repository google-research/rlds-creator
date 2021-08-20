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

"""Helper class for replaying an episode."""

import abc
import datetime
from typing import Optional, Sequence, Union

from rlds_creator import episode_storage
from rlds_creator import storage as study_storage
from rlds_creator import study_pb2
from rlds_creator import utils


class Replay(abc.ABC):
  """Encapsulates an episode and related data for replay."""

  def __init__(self, study_spec: study_pb2.StudySpec,
               env_spec: study_pb2.EnvironmentSpec, episode: study_pb2.Episode,
               steps: Optional[Sequence[episode_storage.StepData]]):
    self._study_spec = study_spec
    self._env_spec = env_spec
    self._episode = episode
    self._steps = steps

  @property
  def episode(self) -> study_pb2.Episode:
    """Returns the episode being replayed."""
    return self._episode

  @property
  def study_spec(self) -> study_pb2.StudySpec:
    """Returns the specification of the study that the episode belongs to."""
    return self._study_spec

  @property
  def env_spec(self) -> study_pb2.EnvironmentSpec:
    """Returns the specification of the environment of the episode."""
    return self._env_spec

  def get_step(self, index: int) -> Optional[episode_storage.StepData]:
    """Returns the step with the specified index."""
    return self._steps[index] if self._steps else None

  @abc.abstractmethod
  def add_episode_tag(self, label: str) -> bool:
    """Adds a tag with the specified label to the episode."""

  @abc.abstractmethod
  def remove_episode_tag(self, label: str) -> bool:
    """Removes the tag(s) with the specified label from the episode."""

  @abc.abstractmethod
  def update_episode(self, notes: str):
    """Updates the episode metadata."""

  @abc.abstractmethod
  def add_step_tag(self, index: int, label: str) -> bool:
    """Adds the tag to the specified step of the episode.

    Args:
      index: 0-based index of the step.
      label: Label of the tag to add.

    Returns:
      True on success.
    """

  @abc.abstractmethod
  def remove_step_tag(self, index: int, label: str) -> bool:
    """Removes the tag from the specified step of the episode.

    Args:
      index: 0-based index of the step.
      label: Label of the tag to remove.

    Returns:
      True on success.
    """


def _add_tag(tags, label: str) -> bool:
  """Adds the tag to the repeated field of tags.

  Args:
    tags: Repeated field of Tags.
    label: Label of the tag to add.

  Returns:
    True if the tag is added.
  """
  for tag in tags:
    if tag.label == label:
      # Episode already has the tag.
      return False
  tags.add().label = label
  return True


def _remove_tag(obj: Union[study_pb2.Episode, study_pb2.StepMetadata],
                label: str) -> bool:
  """Removes the tag from the tags of the object.

  Args:
    obj: An Episode or StepMetadata object.
    label: Label of the tag to remove.

  Returns:
    True if the tag is removed.
  """
  tags = obj.tags
  count = len(tags)
  obj.ClearField('tags')
  obj.tags.extend(tag for tag in tags if tag.label != label)
  return len(obj.tags) != count


class StorageReplay(Replay):
  """Replays an episode from study storage."""

  def __init__(self,
               episode_storage_factory: episode_storage.EpisodeStorageFactory,
               storage: study_storage.Storage, study_id: str, session_id: str,
               episode_id: str):
    """Creates a storage based replay.

    Args:
      episode_storage_factory: Factory to create the episode reader.
      storage: Study storage to load the episode.
      study_id: ID of the study.
      session_id: ID of the session.
      episode_id: ID of the episode.
    """
    self._storage = storage
    episode = self._storage.get_episode(study_id, session_id, episode_id)
    if not episode:
      raise ValueError('Missing episode.')
    study_spec = self._storage.get_study(study_id)
    if not study_spec:
      raise ValueError('Missing study.')
    env_spec = utils.get_env_spec_by_id(study_spec, episode.environment_id)
    if not env_spec:
      raise ValueError('Missing environment.')
    try:
      self._reader = episode_storage_factory.create_reader(episode.storage)
    except IndexError:
      raise ValueError('Missing episode in tag directory.')
    super().__init__(study_spec, env_spec, episode, self._reader.steps)

  def _atomic_update_episode(self, update_fn):
    """Atomically updates the episode calling the update function."""

    updated_episode = None

    def callback(episode: study_pb2.Episode) -> bool:
      nonlocal updated_episode
      if not episode:
        return False
      result = update_fn(episode)
      if result:
        # Keep the updated episode on success.
        updated_episode = episode
      return result

    episode = self._episode
    assert episode  # This is guaranteed.
    result = self._storage.atomic_update_episode(episode.study_id,
                                                 episode.session_id, episode.id,
                                                 callback)
    if updated_episode:
      # Make sure that we have the updated version.
      self._episode = updated_episode
    return result

  def add_episode_tag(self, label: str) -> bool:
    """Adds a tag with the specified label to the episode."""

    def callback(episode: study_pb2.Episode) -> bool:
      return _add_tag(episode.tags, label)

    return self._atomic_update_episode(callback)

  def remove_episode_tag(self, label: str) -> bool:
    """Removes the tag(s) with the specified label from the episode."""

    def callback(episode: study_pb2.Episode) -> bool:
      return _remove_tag(episode, label)

    return self._atomic_update_episode(callback)

  def update_episode(self, notes: str):
    """Updates the episode metadata."""

    def callback(episode: study_pb2.Episode) -> bool:
      if not notes:
        episode.ClearField('notes')
      else:
        episode.notes = notes
      return True

    return self._atomic_update_episode(callback)

  def add_step_tag(self, index: int, label: str) -> bool:
    """Adds the tag to the specified step of the episode."""

    def callback(episode: study_pb2.Episode) -> bool:
      return _add_tag(episode.step_metadata[index].tags, label)

    if index < 0 or index >= len(self._steps):
      raise ValueError('Invalid step.')
    return self._atomic_update_episode(callback)

  def remove_step_tag(self, index: int, label: str) -> bool:
    """Removes the tag from the specified step of the episode."""

    def callback(episode: study_pb2.Episode) -> bool:
      # Accessing the step metadata will create one if it doesn't exist so we
      # first check whether there is a corresponding element in the map.
      if index not in episode.step_metadata:
        return False
      return _remove_tag(episode.step_metadata[index], label)

    if index < 0 or index >= len(self._steps):
      raise ValueError('Invalid step.')
    return self._atomic_update_episode(callback)


class StaticReplay(Replay):
  """Replays a provided sequence of steps."""

  def __init__(self,
               steps: Sequence[episode_storage.StepData],
               session_id: str = 'session',
               episode_id: str = 'episode',
               dt: Optional[datetime.datetime] = None):
    """Creates a file based replay.

    Args:
      steps: A sequence of steps.
      session_id: ID of the session.
      episode_id: ID of the episode.
      dt: Datetime that will be used for the start and end time of the episode.
        If None, then the current time will be used.
    """
    # We use dummy study and environment specs.
    study_spec = study_pb2.StudySpec(id='static', name='Static')
    env_spec = study_pb2.EnvironmentSpec(id='static', name='Static')
    total_reward = sum(
        [step.timestep.reward if step.timestep.reward else 0 for step in steps])
    episode = study_pb2.Episode(
        environment_id=env_spec.id,
        id=episode_id,
        num_steps=len(steps) - 1,
        session_id=session_id,
        state=study_pb2.Episode.STATE_COMPLETED,
        study_id=study_spec.id,
        total_reward=total_reward)
    if not dt:
      dt = datetime.datetime.now()
    episode.start_time.FromDatetime(dt)
    episode.end_time.FromDatetime(dt)
    super().__init__(study_spec, env_spec, episode, steps)

  def add_episode_tag(self, label: str) -> bool:
    raise ValueError('Not supported for file based replays.')

  def remove_episode_tag(self, label: str) -> bool:
    raise ValueError('Not supported for file based replays.')

  def update_episode(self, notes: str):
    raise ValueError('Not supported for file based replays.')

  def add_step_tag(self, index: int, label: str) -> bool:
    raise ValueError('Not supported for file based replays.')

  def remove_step_tag(self, index: int, label: str) -> bool:
    raise ValueError('Not supported for file based replays.')
