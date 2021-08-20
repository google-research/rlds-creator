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

"""DM environment that merges the data from a list of episodes."""

from concurrent import futures
from typing import Any, List, Optional, Sequence, Set

from absl import logging
import dm_env

from rlds_creator import constants
from rlds_creator import episode_storage
from rlds_creator import study_pb2

INTERNAL_STEP_METADATA_KEYS = frozenset([
    constants.METADATA_IMAGE, constants.METADATA_INFO, constants.METADATA_KEYS
])


def _has_tag(step_metadata: study_pb2.StepMetadata, tags: Set[str]) -> bool:
  """Returns true if the step metadata has one of the tags."""
  for tag in step_metadata.tags:
    if tag.label in tags:
      return True
  return False


def _get_step_tags(episodes: List[study_pb2.Episode]) -> Set[str]:
  """Returns the set of step tags used in the episodes."""
  tags = set()
  for episode in episodes:
    for index in episode.step_metadata:
      for tag in episode.step_metadata[index].tags:
        tags.add(tag.label)
  return tags


class Merger(dm_env.Environment):
  """DM environment that merges the data from a list of episodes."""

  def __init__(self,
               episodes: List[study_pb2.Episode],
               episode_storage_factory: episode_storage.EpisodeStorageFactory,
               strip_internal_metadata: bool = False,
               end_of_episode_tags: Optional[Sequence[str]] = None,
               add_step_tags_as_metadata: bool = False,
               num_preloaded_episodes: int = 1):
    """Creates an episode merger.

    Args:
      episodes: List of episodes to merge.
      episode_storage_factory: Factory to create episode reader and writer.
      strip_internal_metadata: If true, then internal episode and step metadata,
        e.g. images and keys for steps and tags and notes for the episode, will
        be stripped and not exposed.
      end_of_episode_tags: List of step tags that denote the end of an episode.
        If a step of an episode is annotated with one of these tags, then the
        episode will be truncated at that step with the corresponding
        observation and reward.
      add_step_tags_as_metadata: If true, then the step tags will be added to
        the custom (meta)data of the steps. For each step tag there will be a
        key of the form tag:[label] with a boolean value indicating whether the
          corresponding step has the tag or not.
      num_preloaded_episodes: Number of episodes that will be preloaded in
        parallel.
    """
    self._episodes = episodes
    self._episode_storage_factory = episode_storage_factory
    self._executor = futures.ThreadPoolExecutor(
        max_workers=num_preloaded_episodes)
    self._reader_futures = [
        self._executor.submit(episode_storage_factory.create_reader,
                              episode.storage) for episode in episodes
    ]
    self._strip_internal_metadata = strip_internal_metadata
    self._end_of_episode_tags = set(end_of_episode_tags or [])
    # We import the specs from the first episode. All episodes will have the
    # same specs.
    self._reader = self._reader_futures[0].result()
    self._reward_spec = self._reader.reward_spec()
    self._discount_spec = self._reader.discount_spec()
    self._observation_spec = self._reader.observation_spec()
    self._action_spec = self._reader.action_spec()
    self._episode_index = 0
    self._episode_num_steps = 0
    self._episode_total_reward = 0
    self._step_index = 0
    self._done = False
    self._steps = None
    self._episode = None
    self._custom_data = None
    self._episode_metadata = None
    if add_step_tags_as_metadata:
      self._step_tags = _get_step_tags(episodes)
    else:
      self._step_tags = set()

  @property
  def done(self) -> bool:
    return self._done

  def next_action(self) -> Any:
    """Returns the next action."""
    return self._steps[self._step_index].action

  def _get_episode_metadata(self):
    """Returns the episode metadata."""
    # Keep the original metadata.
    episode_metadata = self._episode_metadata or {}
    if isinstance(self._custom_data, dict):
      # Remove and merge with the episode metadata in the metadata of the
      # current, i.e. first, step. This is for backward compatibility.
      episode_metadata.update(self._custom_data.pop('episode_metadata', {}))
    # Episode index will be different. We also add episode stats.
    episode_metadata['episode_index'] = self._episode_index
    episode_metadata['num_steps'] = self._episode_num_steps
    episode_metadata['total_reward'] = self._episode_total_reward
    if not self._strip_internal_metadata:
      if self._episode.tags:
        episode_metadata['tags'] = [tag.label for tag in self._episode.tags]
      if self._episode.notes:
        episode_metadata['notes'] = self._episode.notes
    return episode_metadata

  def reset(self) -> dm_env.TimeStep:
    self._episode = self._episodes[self._episode_index]
    logging.debug('Merging episode %r', self._episode)
    assert (len(self._reader_futures) + self._episode_index == len(
        self._episodes))
    self._reader = self._reader_futures.pop(0).result()
    # Reset the steps and the metadata for the current episode.
    self._steps = self._reader.steps
    self._episode_metadata = self._reader.metadata
    self._step_index = 0
    self._episode_num_steps = self._episode.num_steps or len(self._steps) - 1
    self._episode_total_reward = self._episode.total_reward

    # Check for an early termination of the episode based on the step tags.
    if self._end_of_episode_tags:
      # The keys, i.e. step indices, may not be sorted.
      for index in sorted(self._episode.step_metadata):
        step_metadata = self._episode.step_metadata[index]
        if _has_tag(step_metadata, self._end_of_episode_tags):
          logging.info('Episode terminates at step %d.', index)
          self._episode_num_steps = index
          self._episode_total_reward = 0
          # Steps doesn't support del operation.
          for i in range(0, index + 1):
            reward = self._steps[i].timestep.reward
            self._episode_total_reward += reward if reward else 0.0
          break

    return self._step()

  def step(self, action) -> dm_env.TimeStep:
    return self._step()

  def _step(self) -> dm_env.TimeStep:
    """Returns the current timestep and advances to the next step."""
    current_step = self._steps[self._step_index]
    if self._strip_internal_metadata and isinstance(current_step.custom_data,
                                                    dict):
      self._custom_data = {
          k: v
          for k, v in current_step.custom_data.items()
          if k not in INTERNAL_STEP_METADATA_KEYS
      }
    else:
      self._custom_data = current_step.custom_data
    # Add boolean metadata for the step tags.
    if self._step_tags:
      tags = set()
      if self._step_index in self._episode.step_metadata:
        for tag in self._episode.step_metadata[self._step_index].tags:
          tags.add(tag.label)
      self._custom_data = self._custom_data or {}
      for tag in self._step_tags:
        self._custom_data[f'tag:{tag}'] = tag in tags
    timestep = current_step.timestep
    if timestep.first():
      self._episode_metadata = self._get_episode_metadata()
    self._step_index += 1
    if self._step_index > self._episode_num_steps:
      if not timestep.last():
        logging.info('Fixing last step.')
        # The episode is truncated. Step tags will contain additional
        # information.
        timestep = dm_env.truncation(timestep.reward, timestep.observation)
      self._episode_index += 1
      self._done = self._episode_index == len(self._episodes)
    return timestep

  def reward_spec(self):
    return self._reward_spec

  def discount_spec(self):
    return self._discount_spec

  def observation_spec(self):
    return self._observation_spec

  def action_spec(self):
    return self._action_spec

  def close(self):
    self._executor.shutdown()

  def step_fn(self, timestep: dm_env.TimeStep, action: Any,
              env: dm_env.Environment):
    """Called by environment logger to process a step and get its metadata."""
    return self._custom_data

  def episode_metadata_fn(self, timestep: dm_env.TimeStep, action: Any,
                          env: dm_env.Environment):
    """Called by environment logger to get the episode metadata."""
    return self._episode_metadata if timestep.first() else None
