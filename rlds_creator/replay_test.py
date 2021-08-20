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

"""Tests for rlds_creator.replay."""

import datetime
from typing import List

from absl.testing import absltest
import mock
from rlds_creator import episode_storage_factory
from rlds_creator import replay
from rlds_creator import storage
from rlds_creator import study_pb2
from rlds_creator import test_utils

MAX_EPISODE_STEPS = 15


def get_labels(tags) -> List[str]:
  return [tag.label for tag in tags]


def _test_get_step(self):
  """Tests the get_step() method."""
  step = self.replay.get_step(0)
  timestep = step.timestep
  self.assertTrue(timestep.first())
  self.assertEqual((64, 64, 3), timestep.observation.shape)
  self.assertIsNone(timestep.discount)
  self.assertIsNone(timestep.reward)
  custom_data = step.custom_data
  self.assertIn('image', custom_data)
  self.assertIn('keys', custom_data)

  step = self.replay.get_step(MAX_EPISODE_STEPS)
  timestep = step.timestep
  self.assertTrue(timestep.last())


class StorageReplayTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.storage = self.enter_context(
        mock.patch.object(storage, 'Storage', autospec=True))
    root_directory = self.create_tempdir()
    self.episode, _, _ = test_utils.record_single_episode(
        'test',
        'maze',
        root_directory.full_path,
        max_episode_steps=MAX_EPISODE_STEPS)
    self.env_spec = study_pb2.EnvironmentSpec(id=self.episode.environment_id)
    self.study_spec = study_pb2.StudySpec(
        id=self.episode.study_id, environment_specs=[self.env_spec])
    self.episode_storage_factory = (
        episode_storage_factory.EpisodeStorageFactory())

  def create_replay(self):
    self.storage.get_episode.return_value = self.episode
    self.storage.get_study.return_value = self.study_spec
    self.storage.atomic_update_episode.side_effect = self.update_episode
    self.replay = replay.StorageReplay(self.episode_storage_factory,
                                       self.storage, self.episode.study_id,
                                       self.episode.session_id, self.episode.id)

  def test_init(self):
    self.create_replay()
    self.storage.get_episode.assert_called_once_with(self.episode.study_id,
                                                     self.episode.session_id,
                                                     self.episode.id)
    self.storage.get_study.assert_called_once_with(self.episode.study_id)
    self.assertEqual(self.episode, self.replay.episode)
    self.assertEqual(self.study_spec, self.replay.study_spec)
    self.assertEqual(self.env_spec, self.replay.env_spec)
    self.assertLen(self.replay._steps, 16)

  def test_missing_episode(self):
    self.storage.get_episode.return_value = None
    with self.assertRaisesRegex(ValueError, 'Missing episode.'):
      replay.StorageReplay(self.episode_storage_factory, self.storage,
                           self.episode.study_id, self.episode.session_id,
                           self.episode.id)

  def test_missing_study(self):
    self.storage.get_episode.return_value = self.episode
    self.storage.get_study.return_value = None
    with self.assertRaisesRegex(ValueError, 'Missing study.'):
      replay.StorageReplay(self.episode_storage_factory, self.storage,
                           self.episode.study_id, self.episode.session_id,
                           self.episode.id)

  def test_missing_environment(self):
    self.storage.get_episode.return_value = self.episode
    self.storage.get_study.return_value = study_pb2.StudySpec(
        id=self.episode.study_id)
    with self.assertRaisesRegex(ValueError, 'Missing environment.'):
      replay.StorageReplay(self.episode_storage_factory, self.storage,
                           self.episode.study_id, self.episode.session_id,
                           self.episode.id)

  def test_get_step(self):
    self.create_replay()
    _test_get_step(self)

  def update_episode(self, study_id, session_id, episode_id, callback):
    self.assertEqual(self.episode.study_id, study_id)
    self.assertEqual(self.episode.session_id, session_id)
    self.assertEqual(self.episode.id, episode_id)
    return callback(self.episode)

  def test_add_episode_tag(self):
    self.create_replay()
    self.assertTrue(self.replay.add_episode_tag('tag1'))
    self.assertTrue(self.replay.add_episode_tag('tag2'))
    self.assertEqual(['tag1', 'tag2'], get_labels(self.episode.tags))

  def test_add_existing_episode_tag(self):
    self.create_replay()
    self.assertTrue(self.replay.add_episode_tag('tag'))
    self.assertFalse(self.replay.add_episode_tag('tag'))
    self.assertEqual(['tag'], get_labels(self.episode.tags))

  def test_remove_episode_tag(self):
    self.create_replay()
    # Add two tags.
    self.replay.add_episode_tag('tag1')
    self.replay.add_episode_tag('tag2')
    # Remove the first one.
    self.assertTrue(self.replay.remove_episode_tag('tag1'))
    self.assertEqual(['tag2'], get_labels(self.episode.tags))

  def test_remove_missing_episode_tag(self):
    self.create_replay()
    self.assertFalse(self.replay.remove_episode_tag('tag'))

  def test_update_episode(self):
    self.create_replay()
    # Add the notes.
    self.replay.update_episode('notes')
    self.assertEqual('notes', self.episode.notes)
    # Remove the notes.
    self.replay.update_episode('')
    self.assertFalse(self.episode.HasField('notes'))

  def test_add_step_tag(self):
    self.create_replay()
    self.assertTrue(self.replay.add_step_tag(3, 'tag1'))
    self.assertTrue(self.replay.add_step_tag(3, 'tag2'))
    self.assertTrue(self.replay.add_step_tag(4, 'tag1'))
    self.assertSameElements([3, 4], self.episode.step_metadata)
    self.assertEqual(['tag1', 'tag2'],
                     get_labels(self.episode.step_metadata[3].tags))
    self.assertEqual(['tag1'], get_labels(self.episode.step_metadata[4].tags))

  def test_add_existing_step_tag(self):
    self.create_replay()
    self.assertTrue(self.replay.add_step_tag(3, 'tag'))
    self.assertFalse(self.replay.add_step_tag(3, 'tag'))
    self.assertEqual(['tag'], get_labels(self.episode.step_metadata[3].tags))

  def test_add_invalid_step_tag(self):
    self.create_replay()
    with self.assertRaisesRegex(ValueError, 'Invalid step.'):
      self.replay.add_step_tag(16, 'tag')

  def test_remove_step_tag(self):
    self.create_replay()
    # Add two tags.
    self.replay.add_step_tag(3, 'tag1')
    self.replay.add_step_tag(3, 'tag2')
    # Remove the first one.
    self.assertTrue(self.replay.remove_step_tag(3, 'tag1'))
    self.assertEqual(['tag2'], get_labels(self.episode.step_metadata[3].tags))

  def test_remove_missing_step_tag(self):
    self.create_replay()
    # Step doesn't have any tags.
    self.assertFalse(self.replay.remove_step_tag(3, 'tag'))
    # Step has a tag.
    self.replay.add_step_tag(3, 'another_tag')
    self.assertFalse(self.replay.remove_step_tag(3, 'tag'))

  def test_remove_invalid_step_tag(self):
    self.create_replay()
    with self.assertRaisesRegex(ValueError, 'Invalid step.'):
      self.replay.remove_step_tag(16, 'tag')


class StaticReplayTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    root_directory = self.create_tempdir()
    self.episode, _, _ = test_utils.record_single_episode(
        'test',
        'maze',
        root_directory.full_path,
        max_episode_steps=MAX_EPISODE_STEPS)
    factory = episode_storage_factory.EpisodeStorageFactory()
    reader = factory.create_reader(self.episode.storage)
    self._dt = datetime.datetime.now()
    self.replay = replay.StaticReplay(reader.steps, dt=self._dt)

  def test_init(self):
    # Study and environment specs should be dummy.
    self.assertEqual(
        study_pb2.StudySpec(id='static', name='Static'), self.replay.study_spec)
    self.assertEqual(
        study_pb2.EnvironmentSpec(id='static', name='Static'),
        self.replay.env_spec)

    expected_episode = study_pb2.Episode(
        environment_id='static',
        id='episode',
        num_steps=self.episode.num_steps,
        session_id='session',
        state=study_pb2.Episode.STATE_COMPLETED,
        study_id='static',
        total_reward=self.episode.total_reward)
    expected_episode.start_time.FromDatetime(self._dt)
    expected_episode.end_time.FromDatetime(self._dt)

    self.assertEqual(expected_episode, self.replay.episode)

  def test_get_step(self):
    _test_get_step(self)

  def test_add_episode_tag(self):
    with self.assertRaises(ValueError):
      self.replay.add_episode_tag('tag')

  def test_remove_episode_tag(self):
    with self.assertRaises(ValueError):
      self.replay.remove_episode_tag('tag')

  def test_update_episode(self):
    with self.assertRaises(ValueError):
      self.replay.update_episode('notes')

  def test_add_step_tag(self):
    with self.assertRaises(ValueError):
      self.replay.add_step_tag(0, 'tag')

  def test_remove_step_tag(self):
    with self.assertRaises(ValueError):
      self.replay.remove_step_tag(0, 'tag')


if __name__ == '__main__':
  absltest.main()
