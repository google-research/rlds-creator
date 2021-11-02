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

"""Tests for rlds_creator.environment_handler."""

import datetime
import json
import os
import statistics
import time
from typing import Optional
import zipfile

from absl.testing import absltest
from absl.testing import parameterized
import dm_env
import mock
import numpy as np
import PIL.Image
from rlds_creator import client_pb2
from rlds_creator import constants
from rlds_creator import environment
from rlds_creator import environment_handler
from rlds_creator import episode_storage
from rlds_creator import episode_storage_factory
from rlds_creator import replay
from rlds_creator import storage
from rlds_creator import study_pb2
from rlds_creator import test_utils
from rlds_creator.envs import procgen_env

USER_EMAIL = test_utils.USER_EMAIL
OTHER_USER_EMAIL = 'other@test.com'
CONFIG = {'arg': 'value'}
# A 2x2 image.
SAMPLE_IMAGE = np.array([
    [[128, 128, 128], [0, 0, 0]],
    [[0, 0, 0], [255, 255, 255]],
],
                        dtype=np.uint8)
URL_PREFIX = 'http://host'


def encode_image(image, fmt='PNG', **kwargs):
  return environment_handler._encode_image(
      PIL.Image.fromarray(image), format=fmt, **kwargs)


def create_response(**kwargs) -> client_pb2.OperationResponse:
  """Returns the response with specified fields."""
  return client_pb2.OperationResponse(**kwargs)


def response_call(**kwargs):
  """Returns a mock call for the encoded response with the specified fields."""
  return mock.call(create_response(**kwargs))


def sample_env_spec(env_id: str = 'env',
                    name: str = '',
                    sync: bool = True,
                    procgen_id: str = 'maze',
                    **kwargs):
  """Returns a sample environment spec."""
  return study_pb2.EnvironmentSpec(
      id=env_id,
      name=name or env_id,
      sync=sync,
      procgen=study_pb2.EnvironmentSpec.Procgen(
          id=procgen_id, start_level=0, rand_seed=1),
      **kwargs)


def sample_study_spec(study_id: str = 'study',
                      name: str = '',
                      email: str = USER_EMAIL,
                      **kwargs):
  """Returns a sample study spec."""
  return study_pb2.StudySpec(
      id=study_id,
      name=name or study_id,
      creator=study_pb2.User(email=email),
      **kwargs)


def sample_study_spec_with_env():
  return sample_study_spec(environment_specs=[sample_env_spec()])


def sample_study_spec_with_async_env():
  return sample_study_spec(
      environment_specs=[sample_env_spec(procgen_id='coinrun', sync=False)])


def sample_episode(study_id: str = 'study',
                   session_id: str = 'session',
                   episode_id: str = 'episode',
                   email: str = USER_EMAIL,
                   path: Optional[str] = None) -> study_pb2.Episode:
  """Returns a sample episode."""
  episode = study_pb2.Episode(
      study_id=study_id,
      session_id=session_id,
      id=episode_id,
      user=study_pb2.User(email=email))
  if path:
    episode.storage.pickle.path = path
  return episode


class EnvironmentHandler(environment_handler.EnvironmentHandler):
  """Environment handler for the tests."""

  def create_env_from_spec(
      self, env_spec: study_pb2.EnvironmentSpec) -> environment.Environment:
    assert env_spec.WhichOneof('type') == 'procgen'
    return procgen_env.ProcgenEnvironment(env_spec)

  def get_url_for_path(self, path: str) -> str:
    return URL_PREFIX + path

  def send_response(self, response: client_pb2.OperationResponse) -> bool:
    return True


class EnvironmentHandlerTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    self.storage = self.enter_context(
        mock.patch.object(storage, 'Storage', autospec=True))
    self.base_log_dir = self.create_tempdir()
    self.episode_storage_factory = (
        episode_storage_factory.EpisodeStorageFactory())

    self.handler = EnvironmentHandler(
        self.storage,
        study_pb2.User(email=USER_EMAIL),
        CONFIG,
        self.episode_storage_factory,
        self.base_log_dir,
        record_videos=True)
    self.handler.send_response = self.enter_context(
        mock.patch.object(self.handler, 'send_response'))
    # Make sure that mocks do not have any expectations set.
    self._reset_mocks()

  def _reset_mocks(self):
    self.storage.reset_mock()
    self.handler.send_response.reset_mock()

  def send_request(self, **kwargs):
    """Sends the request with the specified fields to the handler."""
    self.handler.handle_request(client_pb2.OperationRequest(**kwargs))

  def assert_response(self, **kwargs):
    """Asserts that the response matches the specified fields."""
    self.assert_responses([response_call(**kwargs)])

  def assert_error_response(self, mesg: str):
    self.assert_response(error=client_pb2.ErrorResponse(mesg=mesg))

  def assert_responses(self, responses):
    """Asserts that the responses sent in the specified order."""
    self.assertSequenceEqual(responses,
                             self.handler.send_response.call_args_list)

  def test_setup(self):
    studies = [sample_study_spec()]
    self.storage.get_studies.return_value = studies
    self.handler.setup()
    # Config and studies should be sent to the client.
    self.storage.get_studies.assert_called_once_with(email=USER_EMAIL)
    self.assert_responses([
        response_call(
            config=client_pb2.ConfigResponse(config=json.dumps(CONFIG))),
        response_call(
            set_studies=client_pb2.SetStudiesResponse(studies=studies))
    ])

  @parameterized.named_parameters(('owner', USER_EMAIL, True),
                                  ('not_owner', OTHER_USER_EMAIL, False))
  def test_get_episode_metadata(self, email, can_delete):
    study_spec = sample_study_spec()
    env_spec = sample_env_spec()
    episode = sample_episode(email=email)
    episode.state = study_pb2.Episode.STATE_COMPLETED
    start_time_secs = 1614855000
    episode.start_time.FromSeconds(start_time_secs)
    episode.end_time.FromSeconds(start_time_secs + 200)
    episode.metadata['video_file'] = '/some/video.mp4'
    self.assertEqual(
        client_pb2.EpisodeMetadata(
            study=study_spec,
            env=env_spec,
            episode=episode,
            duration='3 minutes',
            video_url='http://host/some/video.mp4',
            status='Completed',
            can_delete=can_delete),
        self.handler._get_episode_metadata(study_spec, env_spec, episode))

  def test_set_studies(self):
    studies = [sample_study_spec('study1'), sample_study_spec('study2')]
    self.storage.get_studies.return_value = studies

    self.send_request(set_studies=client_pb2.SetStudiesRequest())

    # The studies of the user should be read from storage and sent.
    self.storage.get_studies.assert_called_once_with(email=USER_EMAIL)
    self.assert_response(
        set_studies=client_pb2.SetStudiesResponse(studies=studies))

  @parameterized.named_parameters(
      ('study_creator', USER_EMAIL, None),
      ('not_study_creator', OTHER_USER_EMAIL, USER_EMAIL))
  def test_select_study(self, creator_email, query_email):
    # A study with two environment.
    env_specs = [sample_env_spec('env1'), sample_env_spec('env2')]
    study_spec = sample_study_spec(
        email=creator_email,
        environment_specs=env_specs,
        state=study_pb2.StudySpec.STATE_ENABLED)
    self.storage.get_study.return_value = study_spec

    # Three existing episodes for the study.
    episodes = [
        study_pb2.Episode(
            id='episode1', study_id='study', environment_id='env1'),
        study_pb2.Episode(
            id='episode2', study_id='study', environment_id='env2'),
        # env3 is not present in the current study spec and should not be sent
        # to the client.
        study_pb2.Episode(
            id='episode3', study_id='study', environment_id='env3')
    ]
    self.storage.get_episodes.return_value = episodes

    self.send_request(
        select_study=client_pb2.SelectStudyRequest(study_id='study'))

    # Study and its episodes should be read from the storage.
    self.storage.get_study.assert_called_once_with('study')
    self.storage.get_episodes.assert_called_once_with(
        'study', email=query_email)
    # A new session should be created.
    (created_session,), _ = self.storage.create_session.call_args
    # Ignored fields.
    created_session.ClearField('id')
    created_session.ClearField('start_time')
    self.assertEqual(
        study_pb2.Session(
            study_id='study',
            user=study_pb2.User(email=USER_EMAIL),
            state=study_pb2.Session.State.STATE_VALID), created_session)
    # Study and episodes should be sent in separate responses.
    self.assert_responses([
        response_call(
            select_study=client_pb2.SelectStudyResponse(study=study_spec)),
        response_call(
            episodes=client_pb2.EpisodesResponse(episodes=[
                self.handler._get_episode_metadata(study_spec, env_specs[0],
                                                   episodes[0]),
                self.handler._get_episode_metadata(study_spec, env_specs[1],
                                                   episodes[1]),
            ]))
    ])

  def test_select_missing_study(self):
    self.storage.get_study.return_value = None
    self.send_request(
        select_study=client_pb2.SelectStudyRequest(study_id='study'))
    self.storage.get_study.assert_called_once_with('study')
    self.assert_error_response('Missing study.')

  def test_select_study_not_accessible(self):
    # Study is created by another user and not enabled.
    study_spec = sample_study_spec(email=OTHER_USER_EMAIL)
    self.storage.get_study.return_value = study_spec
    self.send_request(
        select_study=client_pb2.SelectStudyRequest(study_id='study'))
    self.storage.get_study.assert_called_once_with('study')
    self.assert_error_response('You cannot access this study.')

  def test_select_study_enabled(self):
    # Study is created by another user, but enabled and should be accessible.
    study_spec = sample_study_spec(
        email=OTHER_USER_EMAIL, state=study_pb2.StudySpec.STATE_ENABLED)
    self.storage.get_study.return_value = study_spec
    # No episodes.
    self.storage.get_episodes.return_value = []
    self.send_request(
        select_study=client_pb2.SelectStudyRequest(study_id='study'))
    self.storage.get_study.assert_called_once_with('study')
    self.assert_responses([
        response_call(
            select_study=client_pb2.SelectStudyResponse(study=study_spec)),
        # Episodes response should be empty.
        response_call(episodes=client_pb2.EpisodesResponse())
    ])

  def _select_study(self, study_spec: study_pb2.StudySpec):
    """Selects the study with the specified spec."""
    self.storage.get_study.return_value = study_spec
    self.send_request(
        select_study=client_pb2.SelectStudyRequest(study_id='study'))
    self._reset_mocks()

  def test_select_environment(self):
    env_specs = [sample_env_spec('env1'), sample_env_spec('env2')]
    study_spec = sample_study_spec(environment_specs=env_specs)
    self._select_study(study_spec)

    # Select the second environment.
    self.send_request(
        select_environment=client_pb2.SelectEnvironmentRequest(env_id='env2'))

    # Episode spec should be set and the initial state (i.e. step 0) should be
    # sent. Reward would be 0 and the synced environment is not paused.
    self.assert_responses([
        response_call(pause=client_pb2.PauseResponse(paused=False)),
        response_call(
            step=client_pb2.StepResponse(
                image=self.handler._image,
                episode_index=1,
                episode_steps=0,
                reward=0)),
        # This should be the last response.
        response_call(
            select_environment=client_pb2.SelectEnvironmentResponse(
                study_id='study', env=env_specs[1])),
    ])
    # Sanity check. Keys and action should be reset.
    self.assertEqual({}, self.handler._keys)
    self.assertEqual(environment.UserInput(keys={}), self.handler._user_input)

  def test_select_missing_environment(self):
    self._select_study(sample_study_spec())
    self.send_request(
        select_environment=client_pb2.SelectEnvironmentRequest(env_id='env'))
    self.assert_error_response('Missing environment.')

  def test_select_environment_no_study(self):
    # Selecting an environment should generate an error is there was no study.
    self.send_request(
        select_environment=client_pb2.SelectEnvironmentRequest(env_id='env'))
    self.assert_error_response('No study is selected.')

  def _select_environment(self,
                          study_spec: study_pb2.StudySpec,
                          env_id: str = 'env'):
    """Selects the study and the environment with the specified ID."""
    self._select_study(study_spec)
    self.send_request(
        select_environment=client_pb2.SelectEnvironmentRequest(env_id=env_id))
    self._reset_mocks()

  def test_action(self):
    self._select_environment(sample_study_spec_with_env())

    self.send_request(action=client_pb2.ActionRequest(keys=['ArrowUp']))

    # New state of the environment should be sent. Step should be 1.
    self.assert_response(
        step=client_pb2.StepResponse(
            image=self.handler._image,
            episode_index=1,
            episode_steps=1,
            reward=0))
    # Sanity check. Keys should contain the canonical code, ArrowUp -> Up.
    self.assertEqual({'Up': 1}, self.handler._keys)
    self.assertEqual(
        environment.UserInput(keys={'Up': 1}), self.handler._user_input)

  def test_action_sync_no_keys(self):
    self._select_environment(sample_study_spec_with_env())
    self.send_request(action=client_pb2.ActionRequest(keys=[]))
    self.handler.send_response.assert_not_called()

  def test_action_pause(self):
    self._select_environment(sample_study_spec_with_env())
    # Pause. Additional keys should be ignored.
    keys = [environment_handler.PAUSE_KEY, 'ArrowUp']
    self.send_request(action=client_pb2.ActionRequest(keys=keys))
    # Unpause
    self.send_request(action=client_pb2.ActionRequest(keys=keys))
    self.assert_responses([
        response_call(pause=client_pb2.PauseResponse(paused=True)),
        response_call(pause=client_pb2.PauseResponse(paused=False))
    ])

  def test_action_reset(self):
    self._select_environment(sample_study_spec_with_env())
    # Enter key resets the episode. Additional keys should be ignored.
    self.send_request(
        action=client_pb2.ActionRequest(keys=['Enter', 'ArrowUp']))
    # Environment should be paused and the confirmation request should be sent.
    self.handler.send_response.assert_has_calls([
        response_call(pause=client_pb2.PauseResponse(paused=True)),
        response_call(
            confirm_save=client_pb2.ConfirmSaveResponse(
                mark_as_completed=True)),
    ])

  def test_action_pause_async(self):
    self._select_environment(sample_study_spec_with_async_env())
    # Environment will be initially in paused state. Unpause.
    self.send_request(
        action=client_pb2.ActionRequest(keys=[environment_handler.PAUSE_KEY]))
    # Sanity check.
    self.assertFalse(self.handler._paused)
    time.sleep(0.5)
    self._reset_mocks()
    self.send_request(
        action=client_pb2.ActionRequest(keys=[environment_handler.PAUSE_KEY]))
    self.handler.send_response.assert_has_calls(
        [response_call(pause=client_pb2.PauseResponse(paused=True))])

  def test_action_gamepad(self):
    self._select_environment(sample_study_spec_with_env())
    self.send_request(
        action=client_pb2.ActionRequest(
            keys=['ArrowUp'],
            gamepad_input=client_pb2.GamepadInput(
                buttons={
                    0: client_pb2.GamepadInput.Button(pressed=True, value=1.0),
                    2: client_pb2.GamepadInput.Button(pressed=True, value=0.5)
                },
                axes={
                    1: 0.25,
                    4: 0.5
                },
                id='my_controller')))
    # Both keyboard and gamepad input should be present.
    self.assertEqual(
        {
            'Axis1': 0.25,
            'Axis4': 0.5,
            'Button0': 1,
            'Button2': 0.5,
            'Up': 1
        }, self.handler._keys)
    # Controller ID should be set in the episode.
    self.assertEqual('my_controller', self.handler._episode.controller_id)

  def test_async_env(self):
    self._select_environment(sample_study_spec_with_async_env())
    # Async environment should be in paused state.
    self.assertTrue(self.handler._paused)
    # Set frame rate to 10 (i.e. 10 steps per second).
    self.send_request(set_fps=client_pb2.SetFpsRequest(fps=10))

    steps = []
    timestamps = []

    def send_fn(request: client_pb2.OperationResponse):
      if request.WhichOneof('type') == 'step':
        steps.append(request.step.episode_steps)
        timestamps.append(time.perf_counter())
      return True

    # Unpause the environment.
    self.handler.send_response.side_effect = send_fn
    self.send_request(
        action=client_pb2.ActionRequest(keys=[environment_handler.PAUSE_KEY]))
    time.sleep(1)
    # Number of step responses should be close to 10.
    num_steps = len(steps)
    self.assertBetween(num_steps, 9, 11)
    # Step indices should be sequential starting from 1 (0 is sent at reset).
    self.assertSequenceEqual(range(1, num_steps + 1), steps)
    # Time between each step should be close to 100ms.
    latency = [timestamps[i] - timestamps[i - 1] for i in range(1, num_steps)]
    self.assertBetween(statistics.mean(latency), 0.09, 0.11)

  @parameterized.named_parameters(
      ('accept_completed', True, True, study_pb2.Episode.STATE_COMPLETED),
      ('accept_not_completed', True, False, study_pb2.Episode.STATE_CANCELLED),
      ('reject', False, True, study_pb2.Episode.STATE_REJECTED),
  )
  def test_save_episode(self, accept: bool, mark_as_completed: bool,
                        state: study_pb2.Episode.State):
    env_spec = sample_env_spec()
    study_spec = sample_study_spec(environment_specs=[env_spec])
    self._select_environment(study_spec)
    session_id = self.handler._session.id

    # Take dummy actions.
    keys = ['ArrowUp', 'ArrowRight', 'ArrowDown', 'ArrowLeft']
    num_steps = len(keys)
    for key in keys:
      self.send_request(action=client_pb2.ActionRequest(keys=[key]))
    self._reset_mocks()

    self.send_request(
        save_episode=client_pb2.SaveEpisodeRequest(
            accept=accept, mark_as_completed=mark_as_completed))

    episode_id = '1.0'
    tag_directory = os.path.join(
        self.base_log_dir, 'study', session_id,
        '' if state == study_pb2.Episode.STATE_COMPLETED else 'ignored', 'env',
        episode_id)
    # Episode should have its IDs and storage set.
    expected_episode = study_pb2.Episode(
        id=episode_id,
        study_id='study',
        environment_id='env',
        user=study_pb2.User(email=USER_EMAIL),
        session_id=session_id,
        state=state,
        num_steps=num_steps,
        total_reward=0,
        storage=study_pb2.Episode.Storage(
            pickle=study_pb2.Episode.Storage.Pickle(
                path=os.path.join(tag_directory, '0.pkl'))))

    # Check that the episode is stored.
    (episode,), _ = self.storage.create_episode.call_args

    # Start and end time should be set.
    self.assertTrue(episode.HasField('start_time'))
    self.assertTrue(episode.HasField('end_time'))
    # Path of the video file should be present in the metadata.
    self.assertEqual(
        os.path.join(tag_directory, 'video.mp4'),
        episode.metadata['video_file'])

    # Episode metadata should be sent to the client and a new episode should
    # start (i.e. episode index should be 2).
    self.assert_responses([
        response_call(
            save_episode=client_pb2.SaveEpisodeResponse(
                episode=self.handler._get_episode_metadata(
                    study_spec, env_spec, episode))),
        response_call(pause=client_pb2.PauseResponse(paused=False)),
        response_call(
            step=client_pb2.StepResponse(
                image=self.handler._image,
                episode_index=2,
                episode_steps=0,
                reward=0)),
    ])

    for ignored_fields in ['start_time', 'end_time', 'metadata']:
      episode.ClearField(ignored_fields)
    self.assertEqual(expected_episode, episode)

    # Check that the episode is logged properly.
    r = self.episode_storage_factory.create_reader(episode.storage)
    steps = r.steps
    self.assertLen(steps, num_steps + 1)

    denv = self.handler._env.env()
    self.assertEqual(denv.observation_spec(), r.observation_spec())
    self.assertEqual(denv.action_spec(), r.action_spec())
    self.assertEqual(denv.reward_spec(), r.reward_spec())
    self.assertEqual(denv.discount_spec(), r.discount_spec())

    # User actions and images should be present in the step metadata.
    mapped_keys = [None, 'Up', 'Right', 'Down', 'Left']
    for index, key in enumerate(mapped_keys):
      step = steps[index]
      self.assertEqual(step.custom_data['keys'], {key: 1} if key else {})
      self.assertIn('image', step.custom_data)
      if index > 0:
        # Step information should be present info custom data.
        self.assertIn('level_complete', step.custom_data['info'])

  def test_set_fps(self):
    fps = constants.ASYNC_FPS  # Default frames/sec.
    self.assertEqual(fps, self.handler._fps)
    # Change the frame rate.
    self.send_request(set_fps=client_pb2.SetFpsRequest(fps=fps + 3))
    self.assertEqual(fps + 3, self.handler._fps)

  def test_set_quality(self):
    self.assertEqual('web_low', self.handler._quality)  # Default preset.
    # Change the image quality to medium and high.
    self.send_request(
        set_quality=client_pb2.SetQualityRequest(
            quality=client_pb2.SetQualityRequest.QUALITY_MEDIUM))
    self.assertEqual('web_medium', self.handler._quality)
    self.send_request(
        set_quality=client_pb2.SetQualityRequest(
            quality=client_pb2.SetQualityRequest.QUALITY_HIGH))
    self.assertEqual('web_high', self.handler._quality)

  @parameterized.named_parameters(('paused_sync', True, True),
                                  ('paused_async', True, False),
                                  ('unpaused_sync', False, True))
  @mock.patch.object(environment, 'Environment', autospec=True)
  def test_set_camera(self, paused, sync, mock_env):
    mock_env.set_camera.return_value = environment.Camera(2, 'name')
    mock_env.render.return_value = SAMPLE_IMAGE
    # Paused environment.
    self.handler._env = mock_env
    self.handler._paused = paused
    self.handler._sync = sync
    self.send_request(set_camera=client_pb2.SetCameraRequest(index=2))
    self.assert_responses([
        response_call(
            set_camera=client_pb2.SetCameraResponse(index=2, name='name')),
        # Image should also be updated.
        response_call(
            step=client_pb2.StepResponse(
                image=encode_image(
                    SAMPLE_IMAGE, fmt='JPEG', quality=self.handler._quality),
                episode_index=0,
                episode_steps=0)),
    ])

  @mock.patch.object(environment, 'Environment', autospec=True)
  def test_set_camera_async(self, mock_env):
    mock_env.set_camera.return_value = environment.Camera(2, 'name')
    self.handler._env = mock_env
    # Async environment and not paused.
    self.handler._paused = False
    self.handler._sync = False
    self.send_request(set_camera=client_pb2.SetCameraRequest(index=2))
    self.assert_response(
        set_camera=client_pb2.SetCameraResponse(index=2, name='name'))
    mock_env.render.assert_not_called()

  def test_save_existing_study(self):
    env_spec = sample_env_spec()
    study_spec = sample_study_spec(
        state=study_pb2.StudySpec.STATE_ENABLED, environment_specs=[env_spec])
    study_spec.creation_time.GetCurrentTime()

    # Existing study with different creation time and state.
    existing_study_spec = sample_study_spec()  # Without environment.
    existing_study_spec.creation_time.FromDatetime(
        datetime.datetime(2021, 1, 2))
    existing_study_spec.state = study_pb2.StudySpec.STATE_DISABLED
    self.storage.get_study.return_value = existing_study_spec

    self.send_request(save_study=client_pb2.SaveStudyRequest(study=study_spec))

    # The updated study spec should preserve the creation time and state of the
    # existing one.
    updated_study_spec = study_spec
    updated_study_spec.creation_time.CopyFrom(existing_study_spec.creation_time)
    updated_study_spec.state = study_pb2.StudySpec.STATE_DISABLED

    # Existing study spec should be read from the storage and the updated
    # version should be saved.
    self.storage.get_study.assert_called_once_with('study')
    (study_spec,), _ = self.storage.update_study.call_args
    self.assertEqual(updated_study_spec, study_spec)

    # The response will be empty.
    self.assert_response(save_study=client_pb2.SaveStudyResponse())

  def test_save_missing_study(self):
    self.storage.get_study.return_value = None
    self.send_request(
        save_study=client_pb2.SaveStudyRequest(study=sample_study_spec()))
    self.assert_error_response('Missing study.')

  def test_save_existing_study_not_creator(self):
    self.storage.get_study.return_value = sample_study_spec(
        email=OTHER_USER_EMAIL)
    self.send_request(
        save_study=client_pb2.SaveStudyRequest(study=sample_study_spec()))
    self.assert_error_response('You cannot modify this study.')

  def test_save_new_study(self):
    study_spec = sample_study_spec(
        study_id=None,
        email=OTHER_USER_EMAIL,
        environment_specs=[sample_env_spec()])
    self.send_request(save_study=client_pb2.SaveStudyRequest(study=study_spec))

    self.storage.get_study.assert_not_called()

    # The creator email should be set to that of the active user.
    study_spec.creator.email = USER_EMAIL
    (created_study_spec,), _ = self.storage.create_study.call_args
    self.assertEqual(study_spec, created_study_spec)

    self.assert_response(save_study=client_pb2.SaveStudyResponse())

  @parameterized.named_parameters(
      ('enable', True, study_pb2.StudySpec.STATE_ENABLED),
      ('disable', False, study_pb2.StudySpec.STATE_DISABLED))
  def test_enable_study(self, enable, state):
    self.storage.get_study.return_value = sample_study_spec()
    self.send_request(
        enable_study=client_pb2.EnableStudyRequest(
            study_id='study', enable=enable))
    # State of the study should be updated in storage and sent to the client.
    self.storage.update_study_state.assert_called_once_with('study', state)
    self.assert_response(
        enable_study=client_pb2.EnableStudyResponse(
            study_id='study', enabled=enable))

  def test_enable_missing_study(self):
    self.storage.get_study.return_value = None
    self.send_request(
        enable_study=client_pb2.EnableStudyRequest(study_id='study'))
    self.assert_error_response('Missing study.')

  @mock.patch.object(replay, 'StorageReplay', autospec=True)
  def test_replay_episode(self, storage_replay):
    env_spec = sample_env_spec()
    storage_replay.return_value.env_spec = env_spec

    study_spec = sample_study_spec(environment_specs=[env_spec])
    storage_replay.return_value.study_spec = study_spec

    # An episode with two steps. The total reward matches that of the steps
    # below.
    episode = study_pb2.Episode(
        id='episode',
        study_id='study',
        environment_id='env',
        session_id='session',
        state=study_pb2.Episode.STATE_COMPLETED,
        num_steps=2,
        total_reward=0.3)
    storage_replay.return_value.episode = episode

    # Observations, actions and step metadata are not used.
    steps = [
        episode_storage.StepData(
            dm_env.TimeStep(dm_env.StepType.FIRST, None, None, None), None),
        episode_storage.StepData(
            dm_env.TimeStep(dm_env.StepType.MID, 0.1, 1.0, None), None),
        episode_storage.StepData(
            dm_env.TimeStep(dm_env.StepType.LAST, 0.2, 0.0, None), None),
    ]
    storage_replay.return_value.get_step.side_effect = (
        lambda index: steps[index])

    self.send_request(
        replay_episode=client_pb2.ReplayEpisodeRequest(
            ref=client_pb2.EpisodeRef(
                study_id='study', session_id='session', episode_id='episode')))

    # Store replay object should be created with the episode reference.
    storage_replay.assert_called_once_with(self.episode_storage_factory,
                                           self.storage, 'study', 'session',
                                           'episode')
    # Episode metadata and the step rewards should be sent to the client.
    self.assert_response(
        replay_episode=client_pb2.ReplayEpisodeResponse(
            episode=self.handler._get_episode_metadata(study_spec, env_spec,
                                                       episode),
            step_rewards=[0, 0.1, 0.2]))

  @parameterized.named_parameters(
      ('non_dict_obs', [1, 2, 3], client_pb2.Data(json_encoded='[1, 2, 3]')),
      ('dict_obs', {
          'a': 1,
          'b': [2, 3],
          'c': SAMPLE_IMAGE
      },
       client_pb2.Data(
           json_encoded='{"a": 1, "b": [2, 3]}',
           images=[
               client_pb2.Data.Image(
                   name='c', image=encode_image(SAMPLE_IMAGE))
           ])),
      ('image_obs', SAMPLE_IMAGE,
       client_pb2.Data(
           images=[client_pb2.Data.Image(image=encode_image(SAMPLE_IMAGE))])),
  )
  @mock.patch.object(replay, 'Replay', autospec=True)
  def test_replay_step(self, obs, obs_data, mock_replay):
    """Tests a replay step with the specified observation."""
    # Inject the mock replay to the environment handler.
    episode = sample_episode()
    step_metadata = episode.step_metadata[2]
    step_metadata.tags.add().label = 'tag1'
    step_metadata.tags.add().label = 'tag2'
    mock_replay.episode = episode
    self.handler._replay = mock_replay

    action = 0.123
    mock_replay.get_step.return_value = episode_storage.StepData(
        dm_env.TimeStep(dm_env.StepType.MID, 0.1, 1.0, obs), action, {
            'keys': {
                'Up': 1,
                'Right': 1
            },
            'image': b'image'
        })

    self.send_request(replay_step=client_pb2.ReplayStepRequest(index=2))

    # get_step() should be called with the specified index.
    mock_replay.get_step.assert_called_once_with(2)
    # Keys image and tags should be present. Action is always json encoded.
    self.assert_response(
        replay_step=client_pb2.ReplayStepResponse(
            index=2,
            image=b'image',
            keys={
                'Up': 1,
                'Right': 1
            },
            reward=0.1,
            observation=obs_data,
            action=client_pb2.Data(json_encoded='0.123'),
            tags=['tag1', 'tag2']))

  @parameterized.named_parameters(('success', True), ('failure', False))
  @mock.patch.object(replay, 'Replay', autospec=True)
  def test_update_replay_episode(self, success, mock_replay):
    mock_replay.update_episode.return_value = success
    self.handler._replay = mock_replay
    self.send_request(
        update_replay_episode=client_pb2.UpdateReplayEpisodeRequest(
            notes='notes'))
    mock_replay.update_episode.assert_called_once_with('notes')
    self.assert_response(
        update_replay_episode=client_pb2.UpdateReplayEpisodeResponse(
            success=success))

  def test_update_replay_episode_no_replay(self):
    self.send_request(
        update_replay_episode=client_pb2.UpdateReplayEpisodeRequest(
            notes='notes'))
    self.assert_response(
        update_replay_episode=client_pb2.UpdateReplayEpisodeResponse(
            success=False))

  @parameterized.named_parameters(('success', True), ('failure', False))
  @mock.patch.object(replay, 'Replay', autospec=True)
  def test_add_episode_tag(self, success, mock_replay):
    mock_replay.add_episode_tag.return_value = success
    self.handler._replay = mock_replay
    self.send_request(
        add_episode_tag=client_pb2.AddEpisodeTagRequest(tag='tag'))
    mock_replay.add_episode_tag.assert_called_once_with('tag')
    self.assert_response(
        add_episode_tag=client_pb2.AddEpisodeTagResponse(
            tag='tag', success=success))

  def test_add_episode_tag_no_replay(self):
    self.send_request(
        add_episode_tag=client_pb2.AddEpisodeTagRequest(tag='tag'))
    self.assert_response(
        add_episode_tag=client_pb2.AddEpisodeTagResponse(
            tag='tag', success=False))

  @parameterized.named_parameters(('success', True), ('failure', False))
  @mock.patch.object(replay, 'Replay', autospec=True)
  def test_remove_episode_tag(self, success, mock_replay):
    mock_replay.remove_episode_tag.return_value = success
    self.handler._replay = mock_replay
    self.send_request(
        remove_episode_tag=client_pb2.RemoveEpisodeTagRequest(tag='tag'))
    mock_replay.remove_episode_tag.assert_called_once_with('tag')
    self.assert_response(
        remove_episode_tag=client_pb2.RemoveEpisodeTagResponse(
            tag='tag', success=success))

  def test_remove_episode_tag_no_replay(self):
    self.send_request(
        remove_episode_tag=client_pb2.RemoveEpisodeTagRequest(tag='tag'))
    self.assert_response(
        remove_episode_tag=client_pb2.RemoveEpisodeTagResponse(
            tag='tag', success=False))

  @parameterized.named_parameters(('success', True), ('failure', False))
  @mock.patch.object(replay, 'Replay', autospec=True)
  def test_add_step_tag(self, success, mock_replay):
    mock_replay.add_step_tag.return_value = success
    self.handler._replay = mock_replay
    self.send_request(
        add_step_tag=client_pb2.AddStepTagRequest(index=2, tag='tag'))
    mock_replay.add_step_tag.assert_called_once_with(2, 'tag')
    self.assert_response(
        add_step_tag=client_pb2.AddStepTagResponse(
            index=2, tag='tag', success=success))

  def test_add_step_tag_no_replay(self):
    self.send_request(
        add_step_tag=client_pb2.AddStepTagRequest(index=2, tag='tag'))
    self.assert_response(
        add_step_tag=client_pb2.AddStepTagResponse(
            index=2, tag='tag', success=False))

  @parameterized.named_parameters(('success', True), ('failure', False))
  @mock.patch.object(replay, 'Replay', autospec=True)
  def test_remove_step_tag(self, success, mock_replay):
    mock_replay.remove_step_tag.return_value = success
    self.handler._replay = mock_replay
    self.send_request(
        remove_step_tag=client_pb2.RemoveStepTagRequest(index=2, tag='tag'))
    mock_replay.remove_step_tag.assert_called_once_with(2, 'tag')
    self.assert_response(
        remove_step_tag=client_pb2.RemoveStepTagResponse(
            index=2, tag='tag', success=success))

  def test_remove_step_tag_no_replay(self):
    self.send_request(
        remove_step_tag=client_pb2.RemoveStepTagRequest(index=2, tag='tag'))
    self.assert_response(
        remove_step_tag=client_pb2.RemoveStepTagResponse(
            index=2, tag='tag', success=False))

  @parameterized.named_parameters(
      ('dir', False, None),
      ('archive', True, None),
      ('dir_no_end', False, ['bogus']),
      ('archive_no_end', True, ['bogus']),
      ('dir_end', False, ['bogus', 'end']),
      ('archive_end', True, ['bogus', 'end']),
  )
  def test_download_episodes(self, archive, end_of_episode_tags):
    root_directory = self.create_tempdir()
    episode_ids = ['one', 'two']
    episodes = {}
    for episode_id in episode_ids:
      episode, _, _ = test_utils.record_single_episode(
          episode_id, 'maze', os.path.join(root_directory, episode_id), 15)
      episodes[episode_id] = episode

    def get_episode(study_id, session_id, episode_id):
      self.assertEqual(study_id, 'study')
      self.assertEqual(session_id, 'session')
      episode = episodes[episode_id]
      episode.step_metadata[5].tags.add().label = 'end'
      return episode

    self.storage.get_episode.side_effect = get_episode

    refs = [
        client_pb2.EpisodeRef(
            study_id=e.study_id, session_id=e.session_id, episode_id=e.id)
        for e in episodes.values()
    ]
    self.send_request(
        download_episodes=client_pb2.DownloadEpisodesRequest(
            refs=refs, archive=archive,
            end_of_episode_tags=end_of_episode_tags))

    # There should be two download responses.
    ((response1,), _), ((response2,), _) = (
        self.handler.send_response.call_args_list)

    self.assertEqual(
        create_response(
            download_episodes=client_pb2.DownloadEpisodesResponse(progress=50)),
        response1)

    download_episodes = response2.download_episodes
    self.assertTrue(download_episodes.url.startswith(URL_PREFIX))
    self.assertEqual(100, download_episodes.progress)

    path = download_episodes.url[len(URL_PREFIX):]
    if archive:
      # The path should point to the ZIP file.
      self.assertTrue(os.path.isfile(path))
      temp_dir = self.create_tempdir()
      # Extract the contents to a temporary directory.
      with zipfile.ZipFile(path) as zf:
        zf.extractall(temp_dir)
      path = temp_dir.full_path
    else:
      # The path should point to the directory.
      self.assertTrue(os.path.isdir(path))

    # Read the generated dataset and do the sanity check.
    if end_of_episode_tags and 'end' in end_of_episode_tags:
      # Episodes should be truncated if there is a matching end of episode tag
      # in the request.
      episode_length = [6, 6]
    else:
      episode_length = [16, 16]
    for i in range(2):
      spec = study_pb2.Episode.Storage(
          pickle=study_pb2.Episode.Storage.Pickle(
              path=os.path.join(path, f'{i}.pkl')))
      r = self.episode_storage_factory.create_reader(spec)
      self.assertLen(r.steps, episode_length[i])
      self.assertContainsSubset(
          [
              # Dataset metadata.
              'episode_id',
              'rlds_creator:env_id',
              'rlds_creator:study_id',
              # Episode specific metadata.
              'agent_id',
              'num_steps',
              'total_reward',
          ],
          r.metadata)

  def test_download_episodes_different_study(self):
    self.storage.get_episode.return_value = study_pb2.Episode()
    self.send_request(
        download_episodes=client_pb2.DownloadEpisodesRequest(refs=[
            client_pb2.EpisodeRef(
                study_id='study1', session_id='session', episode_id='1'),
            client_pb2.EpisodeRef(
                study_id='study2', session_id='session', episode_id='2')
        ]))
    self.assert_error_response(
        'Request failed: Episodes are not from the same study.')

  def test_download_episodes_missing_episode(self):
    self.storage.get_episode.return_value = None
    self.send_request(
        download_episodes=client_pb2.DownloadEpisodesRequest(refs=[
            client_pb2.EpisodeRef(
                study_id='study', session_id='session', episode_id='1')
        ]))
    self.assert_error_response(
        'Request failed: One of the episodes is missing.')

  def test_download_episodes_different_environment(self):
    self.storage.get_episode.side_effect = [
        study_pb2.Episode(environment_id='env1'),
        study_pb2.Episode(environment_id='env2')
    ]
    self.send_request(
        download_episodes=client_pb2.DownloadEpisodesRequest(refs=[
            client_pb2.EpisodeRef(
                study_id='study', session_id='session', episode_id='1'),
            client_pb2.EpisodeRef(
                study_id='study', session_id='session', episode_id='2')
        ]))
    self.assert_error_response(
        'Request failed: Episodes must be from the same environment.')

  @parameterized.named_parameters(('success', True), ('failure', False))
  def test_delete_episode(self, success):
    f = self.create_tempfile()
    path = f.full_path
    episode = sample_episode(path=path)
    self.storage.get_episode.return_value = episode
    self.storage.delete_episode.return_value = success

    ref = client_pb2.EpisodeRef(
        study_id=episode.study_id,
        session_id=episode.session_id,
        episode_id=episode.id)
    self.send_request(delete_episode=client_pb2.DeleteEpisodeRequest(ref=ref))

    self.storage.delete_episode.assert_called_once_with(episode.study_id,
                                                        episode.session_id,
                                                        episode.id)
    self.assert_response(
        delete_episode=client_pb2.DeleteEpisodeResponse(
            ref=ref, success=success))
    # Tag directory should be removed if the delete operation was successful.
    self.assertIsNot(os.path.exists(path), success)

  def test_delete_missing_episode(self):
    self.storage.get_episode.return_value = None
    self.send_request(
        delete_episode=client_pb2.DeleteEpisodeRequest(
            ref=client_pb2.EpisodeRef(
                study_id='study', session_id='session', episode_id='episode')))
    self.assert_error_response('Missing episode.')

  def test_delete_episode_not_allowed(self):
    episode = sample_episode(email=OTHER_USER_EMAIL)
    self.storage.get_episode.return_value = episode

    self.send_request(
        delete_episode=client_pb2.DeleteEpisodeRequest(
            ref=client_pb2.EpisodeRef(
                study_id=episode.study_id,
                session_id=episode.session_id,
                episode_id=episode.id)))
    self.assert_error_response('You cannot delete this episode.')


if __name__ == '__main__':
  absltest.main()
