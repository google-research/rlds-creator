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

"""Generic tests for the storage layer."""

import datetime
from typing import Optional, Tuple

from absl.testing import parameterized
from rlds_creator import storage
from rlds_creator import study_pb2


def sample_study_spec(
    name: str = 'test',
    state: study_pb2.StudySpec.State = study_pb2.StudySpec.STATE_ENABLED,
    email: str = 'user@test.com') -> study_pb2.StudySpec:
  """Returns a sample study with the specified properties."""
  return study_pb2.StudySpec(
      id='ignored',
      name=name,
      description=f'{name} study',
      state=state,
      creator=study_pb2.User(email=email),
      environment_specs=[
          study_pb2.EnvironmentSpec(id='env1', name='env 1'),
          study_pb2.EnvironmentSpec(id='env2', name='env 2')
      ])


def sample_session(
    study_id: str,
    session_id: str = 'test',
    state: study_pb2.Session.State = study_pb2.Session.STATE_VALID,
    start_time: Optional[datetime.datetime] = None,
    email: str = 'user@test.com') -> study_pb2.Session:
  """Returns a sample session with the specified properties."""
  session = study_pb2.Session(
      study_id=study_id,
      id=session_id,
      state=state,
      user=study_pb2.User(email=email))
  if not start_time:
    start_time = datetime.datetime.now()
  session.start_time.FromDatetime(start_time)
  return session


def sample_episode(
    study_id: str,
    session_id: str,
    episode_id: str = 'test',
    state: study_pb2.Episode.State = study_pb2.Episode.STATE_COMPLETED,
    start_time: Optional[datetime.datetime] = None,
    email: str = 'user@test.com',
    num_steps: int = 100,
    total_reward: float = 1.0) -> study_pb2.Episode:
  """Returns a sample episode with the specified properties."""
  episode = study_pb2.Episode(
      study_id=study_id,
      session_id=session_id,
      id=episode_id,
      state=state,
      user=study_pb2.User(email=email),
      num_steps=num_steps,
      total_reward=total_reward)
  if not start_time:
    start_time = datetime.datetime.now()
  episode.start_time.FromDatetime(start_time)
  return episode


class StorageTest(parameterized.TestCase):
  """Test suite for the storage layer.

  Storage implementations can inherit from StorageTest and define storage()
  property to run the test suite.
  """

  @property
  def storage(self) -> storage.Storage:
    """Returns the storage to test."""
    raise ValueError('Not implemented.')

  def test_create_study(self):
    """Tests creating a study."""
    study_spec = sample_study_spec()

    now = datetime.datetime.now()
    study_id = self.storage.create_study(study_spec)
    # Study ID must be a 32 char string.
    self.assertLen(study_id, 32)
    self.assertEqual(study_id, study_spec.id)
    self.assertGreaterEqual(study_spec.creation_time.ToDatetime(), now)

    # Read back the study and check that it is the same.
    self.assertEqual(self.storage.get_study(study_id), study_spec)

  def test_get_study_missing(self):
    """Tests getting a missing study."""
    self.assertIsNone(self.storage.get_study('missing'))

  def test_update_study_state(self):
    """Tests updating the state of a study."""
    study_spec = sample_study_spec()
    study_id = self.storage.create_study(study_spec)
    self.assertEqual(study_pb2.StudySpec.STATE_ENABLED, study_spec.state)

    # Update the state.
    self.storage.update_study_state(study_id,
                                    study_pb2.StudySpec.STATE_DISABLED)

    study_spec = self.storage.get_study(study_id)
    self.assertIsNotNone(study_spec)
    self.assertEqual(study_pb2.StudySpec.STATE_DISABLED, study_spec.state)  # pytype: disable=attribute-error

  def test_update_study_state_missing(self):
    """Tests updating the state of a missing study."""
    with self.assertRaises(ValueError):
      self.storage.update_study_state('missing',
                                      study_pb2.StudySpec.STATE_ENABLED)

  def test_update_study(self):
    """Tests updating a study."""
    study_spec = sample_study_spec()
    study_id = self.storage.create_study(study_spec)
    self.assertEqual(study_pb2.StudySpec.STATE_ENABLED, study_spec.state)
    self.assertEqual('test', study_spec.name)
    creation_time = study_spec.creation_time.ToDatetime()

    study_spec.name = 'changed test'
    study_spec.state = study_pb2.StudySpec.STATE_DISABLED
    study_spec.creation_time.GetCurrentTime()
    self.storage.update_study(study_spec)

    study_spec = self.storage.get_study(study_id)
    self.assertIsNotNone(study_spec)
    assert study_spec  # To disable attribute-error
    self.assertEqual('changed test', study_spec.name)
    # Creation time and status should not change.
    self.assertEqual(study_pb2.StudySpec.STATE_ENABLED, study_spec.state)
    self.assertEqual(creation_time, study_spec.creation_time.ToDatetime())

  def test_update_study_missing(self):
    """Tests updating a missing study."""
    study_spec = sample_study_spec()
    with self.assertRaises(ValueError):
      self.storage.update_study(study_spec)

  def test_get_studies(self):
    """Tests getting the studies."""
    states = [
        study_pb2.StudySpec.STATE_ENABLED, study_pb2.StudySpec.STATE_DISABLED
    ]
    studies = []
    for i in range(5):
      study_spec = sample_study_spec(name=str(i), state=states[i % len(states)])
      self.storage.create_study(study_spec)
      studies.append(study_spec)

    self.assertListEqual(studies, self.storage.get_studies())
    for state in states:
      self.assertListEqual([study for study in studies if study.state is state],
                           self.storage.get_studies(state=state))

  def test_get_studies_by_user(self):
    """Tests getting the studies of a user."""
    studies = [
        sample_study_spec(name='foo1', email='foo'),
        sample_study_spec(name='bar1', email='bar'),
        sample_study_spec(name='foo2', email='foo'),
    ]
    for study_spec in studies:
      self.storage.create_study(study_spec)

    self.assertListEqual([studies[0], studies[2]],
                         self.storage.get_studies(email='foo'))
    self.assertListEqual([studies[1]], self.storage.get_studies(email='bar'))

  def test_create_session(self):
    """Tests creating a session."""
    study_id = self.storage.create_study(sample_study_spec())

    session = sample_session(study_id=study_id)
    self.storage.create_session(session)

    self.assertEqual(self.storage.get_session(study_id, session.id), session)

  @parameterized.named_parameters(
      ('study_id', 'study_id'),
      ('session_id', 'id'),
      ('start_time', 'start_time'),
  )
  def test_create_session_missing_field(self, field_name):
    """Tests creating a session with missing fields."""
    study_id = self.storage.create_study(sample_study_spec())
    session = sample_session(study_id=study_id)
    session.ClearField(field_name)
    with self.assertRaises(ValueError):
      self.storage.create_session(session)

  def test_create_session_missing_study(self):
    """Tests creating a session for a missing study."""
    session = sample_session(study_id='missing')
    with self.assertRaises(ValueError):
      self.storage.create_session(session)

  def test_get_session_missing(self):
    """Tests getting a missing session."""
    study_id = self.storage.create_study(sample_study_spec())
    self.assertIsNone(self.storage.get_session(study_id, 'missing'))

    session = sample_session(study_id)
    self.storage.create_session(session)
    self.assertIsNone(self.storage.get_session('missing', session.id))

  def test_update_session(self):
    """Tests updating a session."""
    study_id = self.storage.create_study(sample_study_spec())

    session = sample_session(study_id=study_id)
    self.storage.create_session(session)
    self.assertEqual(session.state, study_pb2.Session.STATE_VALID)

    session.state = study_pb2.Session.STATE_INVALID
    self.storage.update_session(session)

    self.assertEqual(self.storage.get_session(study_id, session.id), session)
    self.assertEqual(session.state, study_pb2.Session.STATE_INVALID)

  def test_update_missing_session(self):
    """Tests updating a missing session."""
    study_id = self.storage.create_study(sample_study_spec())
    session = sample_session(study_id=study_id)
    with self.assertRaises(ValueError):
      self.storage.update_session(session)

  def init_session(self) -> Tuple[str, str]:
    """Initializes a session and returns the study ID and session ID."""
    study_id = self.storage.create_study(sample_study_spec())
    session = sample_session(study_id=study_id)
    self.storage.create_session(session)
    return study_id, session.id

  def _create_sample_episode(self) -> study_pb2.Episode:
    """Initializes a session and creates a sample episode in the storage."""
    study_id, session_id = self.init_session()
    episode = sample_episode(study_id=study_id, session_id=session_id)
    self.storage.create_episode(episode)
    return episode

  def test_create_episode(self):
    """Tests creating an episode."""
    episode = self._create_sample_episode()

    self.assertEqual(
        self.storage.get_episode(episode.study_id, episode.session_id,
                                 episode.id), episode)

  @parameterized.named_parameters(
      ('study_id', 'study_id'),
      ('session_id', 'session_id'),
      ('episode_id', 'id'),
      ('start_time', 'start_time'),
  )
  def test_create_episode_missing_field(self, field_name):
    """Tests creating an episode with missing fields."""
    study_id, session_id = self.init_session()
    episode = sample_episode(study_id=study_id, session_id=session_id)
    episode.ClearField(field_name)
    with self.assertRaises(ValueError):
      self.storage.create_episode(episode)

  def test_create_episode_missing_session(self):
    """Tests creating an episode for a missing session."""
    study_id = self.storage.create_study(sample_study_spec())
    episode = sample_episode(study_id=study_id, session_id='missing')
    with self.assertRaises(ValueError):
      self.storage.create_episode(episode)

  def test_create_episode_missing_study(self):
    """Tests creating an episode for a missing study."""
    _, session_id = self.init_session()
    episode = sample_episode(study_id='missing', session_id=session_id)
    with self.assertRaises(ValueError):
      self.storage.create_episode(episode)

  def test_create_existing_episode(self):
    """Tests creating an existing episode."""
    episode = self._create_sample_episode()
    with self.assertRaises(ValueError, msg='Episode already exists.'):
      self.storage.create_episode(episode)

  def test_get_episodes(self):
    """Tests getting episodes."""
    study_id, session_id = self.init_session()
    emails = ['user1@', 'user2@']
    episodes = []
    for i in range(5):
      email = emails[i % len(emails)]
      episode = sample_episode(
          study_id, session_id, episode_id=f'test{i}', email=email)
      self.storage.create_episode(episode)
      episodes.append(episode)

    # Episodes will be ordered by decreasing creation timestamp.
    episodes.reverse()

    self.assertListEqual(self.storage.get_episodes(study_id), episodes)

    for email in emails:
      self.assertListEqual(
          [episode for episode in episodes if episode.user.email == email],
          self.storage.get_episodes(study_id, email=email))

  def test_atomic_update_episode(self):
    """Tests atomic update of an episode."""
    episode = self._create_sample_episode()
    study_id, session_id, episode_id = (episode.study_id, episode.session_id,
                                        episode.id)

    def callback(read_episode):
      # Read episode should match the stored one.
      self.assertEqual(read_episode, episode)
      self.assertEqual(read_episode.num_steps, 100)
      # Make a change.
      read_episode.num_steps = 200
      return True

    self.assertTrue(
        self.storage.atomic_update_episode(study_id, session_id, episode_id,
                                           callback))
    # Check that the change was applied.
    episode.num_steps = 200
    self.assertEqual(
        self.storage.get_episode(study_id, session_id, episode_id), episode)

  def test_atomic_update_episode_no_update(self):
    """Tests atomic update of an episode without any changes."""
    episode = self._create_sample_episode()
    study_id, session_id, episode_id = (episode.study_id, episode.session_id,
                                        episode.id)

    def callback(read_episode):
      # Make a change but return false.
      read_episode.num_steps = 200
      return False

    self.assertFalse(
        self.storage.atomic_update_episode(study_id, session_id, episode_id,
                                           callback))
    self.assertEqual(
        self.storage.get_episode(study_id, session_id, episode_id), episode)

  @parameterized.named_parameters(
      ('study_id', 'study_id'),
      ('session_id', 'session_id'),
      ('episode_id', 'id'),
  )
  def test_atomic_update_episode_id_change_not_allowed(self, field_name):
    """Tests trying to change the episode ID in an atomic update."""
    episode = self._create_sample_episode()
    study_id, session_id, episode_id = (episode.study_id, episode.session_id,
                                        episode.id)

    def callback(read_episode):
      setattr(read_episode, field_name, 'changed')
      return True

    self.assertFalse(
        self.storage.atomic_update_episode(study_id, session_id, episode_id,
                                           callback))

  def test_atomic_update_missing_episode(self):
    """Tests atomic update of a missing episode."""

    def callback(unused_episode):
      # Callback should not be called.
      assert False

    self.assertFalse(
        self.storage.atomic_update_episode('study', 'session', 'missing',
                                           callback))

  def test_delete_episode(self):
    """Tests deleting an episode."""
    episode = self._create_sample_episode()
    study_id, session_id, episode_id = (episode.study_id, episode.session_id,
                                        episode.id)
    self.assertIsNotNone(
        self.storage.get_episode(study_id, session_id, episode_id))

    self.assertTrue(
        self.storage.delete_episode(episode.study_id, episode.session_id,
                                    episode.id))
    self.assertIsNone(
        self.storage.get_episode(study_id, session_id, episode_id))
