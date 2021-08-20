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

"""Tests for rlds_creator.merger."""

from absl import logging
from absl.testing import absltest
from absl.testing import parameterized
import numpy.testing as npt

from rlds_creator import constants
from rlds_creator import episode_storage_factory
from rlds_creator import merger
from rlds_creator import pickle_episode_storage
from rlds_creator import study_pb2
from rlds_creator import test_utils


class MergerTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    self._episode_storage_factory = (
        episode_storage_factory.EpisodeStorageFactory())

  @parameterized.parameters((1,), (2,), (4,))
  def test_merge(self, num_preloaded_episodes):
    # Two data sets with 2 and 3 episodes.
    num_dataset_episodes = [2, 3]
    total_num_episodes = sum(num_dataset_episodes)
    env_id = 'maze'
    root_directories = []
    episodes = []
    all_timesteps = []
    all_actions = []
    all_metadatas = []

    def step_fn():
      # Return dummy metadata.
      metadata = {'dummy': len(all_metadatas)}
      all_metadatas.append(metadata)
      return metadata

    dummy = 0

    for num_episodes in num_dataset_episodes:
      root_directory = self.create_tempdir()
      root_directories.append(root_directory)
      env = test_utils.create_env(env_id)
      writer = pickle_episode_storage.PickleEpisodeWriter(
          env.env(), root_directory.full_path)
      for i in range(num_episodes):
        episode, timesteps, actions = test_utils.record_episode(
            writer,
            str(i),
            env_id,
            env,
            step_fn=step_fn,
            episode_metadata={
                'episode_index': 0,
                'dummy': dummy
            })
        logging.info('Created episode %r', episode)
        episodes.append(episode)
        all_timesteps.extend(timesteps)
        all_actions.extend(actions)
        dummy += 1
      writer.close()
    # Add tags and notes to one of the episodes
    episodes[2].tags.extend(
        [study_pb2.Tag(label='tag1'),
         study_pb2.Tag(label='tag2')])
    episodes[2].notes = 'some notes'

    # Number of timesteps per episode will be MAX_EPISODE_STEPS plus the initial
    # timestep.
    self.assertLen(all_timesteps,
                   total_num_episodes * (test_utils.MAX_EPISODE_STEPS + 1))
    self.assertLen(all_actions,
                   total_num_episodes * test_utils.MAX_EPISODE_STEPS)

    m = merger.Merger(
        episodes,
        self._episode_storage_factory,
        num_preloaded_episodes=num_preloaded_episodes)
    # Reward, discount, observation and action specs should match that of the
    # source environment.
    env = test_utils.create_env(env_id).env()
    self.assertEqual(env.reward_spec(), m.reward_spec())
    self.assertEqual(env.discount_spec(), m.discount_spec())
    self.assertEqual(env.observation_spec(), m.observation_spec())
    self.assertEqual(env.action_spec(), m.action_spec())

    # Collect the merged timesteps, actions and step metadata.
    timestep = m.reset()
    num_resets = 1
    timesteps = [timestep]
    episode_metadatas = [m.episode_metadata_fn(timestep, None, env)]
    actions = []
    metadatas = [m.step_fn(timestep, None, env)]
    while not m.done:
      action = m.next_action()
      actions.append(action)
      timestep = m.step(action)
      timesteps.append(timestep)
      metadatas.append(m.step_fn(timestep, action, env))
      if timestep.last() and not m.done:
        timestep = m.reset()
        timesteps.append(timestep)
        metadatas.append(m.step_fn(timestep, None, env))
        episode_metadatas.append(m.episode_metadata_fn(timestep, None, env))
        num_resets += 1

    self.assertEqual(num_resets, total_num_episodes)
    self.assertEqual(len(timesteps), len(all_timesteps))
    # Timesteps should be the same.
    for t1, t2 in zip(timesteps, all_timesteps):
      self.assertEqual(t1.step_type, t2.step_type)
      self.assertEqual(t1.reward, t2.reward)
      self.assertEqual(t1.discount, t2.discount)
      npt.assert_array_equal(t1.observation, t2.observation)
    # Actions should be the same.
    self.assertListEqual(actions, all_actions)
    # Step metadatas should be the same.
    for expected_metadata, metadata in zip(all_metadatas, metadatas):
      npt.assert_array_equal(
          expected_metadata.pop(constants.METADATA_IMAGE),
          metadata.pop(constants.METADATA_IMAGE))
      self.assertDictEqual(expected_metadata, metadata)

    # Check that the episode metadata matches that of the episodes.
    episode_index = 0
    for episode, episode_metadata in zip(episodes, episode_metadatas):
      expected_episode_metadata = {
          'agent_id': test_utils.AGENT_ID,
          'episode_id': episode.id,
          'episode_index': episode_index,
          'num_steps': episode.num_steps,
          'total_reward': episode.total_reward,
          'rlds_creator:env_id': 'maze',
          'rlds_creator:study_id': test_utils.STUDY_ID,
          # The custom episode metadata should be present.
          'dummy': episode_index,
      }
      # Only this episode has tags and notes.
      if episode_index == 2:
        expected_episode_metadata['tags'] = ['tag1', 'tag2']
        expected_episode_metadata['notes'] = episode_metadata['notes']
      self.assertDictEqual(expected_episode_metadata, episode_metadata)
      episode_index += 1

  def test_strip_internal_metadata(self):

    def step_fn():
      # Add internal metadata and some custom ones.
      metadata = {k: k for k in merger.INTERNAL_STEP_METADATA_KEYS}
      metadata['custom1'] = 1
      metadata['custom2'] = 2
      return metadata

    root_directory = self.create_tempdir()
    episode, _, _ = test_utils.record_single_episode(
        'test', 'maze', root_directory.full_path, step_fn=step_fn)
    episode.tags.add().label = 'tag'
    episode.notes = 'test'

    m = merger.Merger([episode],
                      self._episode_storage_factory,
                      strip_internal_metadata=True)
    timestep = m.reset()
    episode_metadata = m.episode_metadata_fn(timestep, None, None)
    # Tag and notes should not be present.
    self.assertDictEqual(
        {
            'agent_id': test_utils.AGENT_ID,
            'episode_id': 'test',
            'episode_index': 0,
            'num_steps': 100,
            'total_reward': 0.0,
            'rlds_creator:env_id': 'maze',
            'rlds_creator:study_id': test_utils.STUDY_ID,
        }, episode_metadata)

    action = m.next_action()
    timestep = m.step(action)
    metadata = m.step_fn(timestep, None, None)
    # Internal metadata should be stripped.
    self.assertDictEqual({'custom1': 1, 'custom2': 2}, metadata)

  @parameterized.parameters(
      (['a', 'c'], 1),
      (['c', 'd'], 2),
      (['d', 'e'], 3),
      (['e'], 100),
      (None, 100),
  )
  def test_end_of_episode_tags(self, end_of_episode_tags, expected_num_steps):
    root_directory = self.create_tempdir()
    episode, _, _ = test_utils.record_single_episode('test', 'maze',
                                                     root_directory.full_path)
    self.assertGreater(episode.num_steps, 3)
    step_metadata = episode.step_metadata
    step_metadata[1].tags.add().label = 'a'
    step_metadata[1].tags.add().label = 'b'
    step_metadata[2].tags.add().label = 'b'
    step_metadata[2].tags.add().label = 'c'
    step_metadata[3].tags.add().label = 'd'

    m = merger.Merger([episode],
                      self._episode_storage_factory,
                      end_of_episode_tags=end_of_episode_tags)
    timestep = m.reset()
    # Episode metadata should match the truncated state if end of episode tags
    # apply.
    episode_metadata = m.episode_metadata_fn(timestep, None, None)
    self.assertDictEqual(
        {
            'agent_id': test_utils.AGENT_ID,
            'episode_id': 'test',
            'episode_index': 0,
            'num_steps': expected_num_steps,
            'rlds_creator:env_id': 'maze',
            'rlds_creator:study_id': test_utils.STUDY_ID,
            # TODO(sertan): Also check the reward.
            'total_reward': 0.0
        },
        episode_metadata)

    num_steps = 0
    while not m.done:
      timestep = m.step(m.next_action())
      num_steps += 1
    self.assertEqual(expected_num_steps, num_steps)
    self.assertTrue(timestep.last())
    if num_steps < 100:
      self.assertEqual(1.0, timestep.discount)

  def test_add_step_tags_as_metadata(self):
    root_directory = self.create_tempdir()
    episode, _, _ = test_utils.record_single_episode('test', 'maze',
                                                     root_directory.full_path)
    self.assertGreater(episode.num_steps, 3)
    step_metadata = episode.step_metadata
    step_metadata[1].tags.add().label = 'tag1'
    step_metadata[1].tags.add().label = 'tag2'
    step_metadata[2].tags.add().label = 'tag3'
    step_metadata[3].tags.add().label = 'end'

    m = merger.Merger([episode],
                      self._episode_storage_factory,
                      end_of_episode_tags=['end'],
                      add_step_tags_as_metadata=True,
                      strip_internal_metadata=True)

    # Collect the step metadata.
    timestep = m.reset()
    custom_data = [m.step_fn(timestep, None, None)]
    while not m.done:
      timestep = m.step(m.next_action())
      data = m.step_fn(timestep, None, None)
      custom_data.append(data)

    self.assertEqual([{
        'tag:end': False,
        'tag:tag1': False,
        'tag:tag2': False,
        'tag:tag3': False
    }, {
        'tag:end': False,
        'tag:tag1': True,
        'tag:tag2': True,
        'tag:tag3': False
    }, {
        'tag:end': False,
        'tag:tag1': False,
        'tag:tag2': False,
        'tag:tag3': True
    }, {
        'tag:end': True,
        'tag:tag1': False,
        'tag:tag2': False,
        'tag:tag3': False
    }], custom_data)


if __name__ == '__main__':
  absltest.main()
