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

"""Handles the interactions between the user and an environment."""

import abc
import base64
import io
import json
import os
import tempfile
import threading
import time
from typing import Any, Dict, Optional, Sequence
import uuid
import zipfile

from absl import logging
import cv2
import dm_env
import humanize
import numpy as np
import PIL.Image
from rlds_creator import client_pb2
from rlds_creator import constants
from rlds_creator import environment
from rlds_creator import environment_wrapper
from rlds_creator import episode_storage
from rlds_creator import file_utils
from rlds_creator import merger
from rlds_creator import replay
from rlds_creator import storage as study_storage
from rlds_creator import study_pb2
from rlds_creator import utils

from google.protobuf import json_format
from google.protobuf import message as proto2_message

EnvType = constants.EnvType

# Mapping from browser key codes. See https://www.w3.org/TR/uievents-key/
_KEY_MAPPING = {
    'ArrowUp': 'Up',
    'ArrowDown': 'Down',
    'ArrowLeft': 'Left',
    'ArrowRight': 'Right',
    'Enter': 'Return',
}

PAUSE_KEY = '/'

# JPEG quality settings. See
# https://pillow.readthedocs.io/en/stable/reference/JpegPresets.html.
_DEFAULT_QUALITY = 'web_low'
_QUALITY_MAPPING = {
    client_pb2.SetQualityRequest.QUALITY_LOW: 'web_low',
    client_pb2.SetQualityRequest.QUALITY_MEDIUM: 'web_medium',
    client_pb2.SetQualityRequest.QUALITY_HIGH: 'web_high'
}

# Number of episodes that will be preloaded in the merger when downloading the
# episodes.
MERGER_NUM_PRELOADED_EPISODES = 4


def _copy_temp_file(temp_file, dest: str):
  """Copies a temporary file to destination path."""
  logging.info('Copying %s to %s.', temp_file.name, dest)
  file_utils.copy(temp_file.name, dest, overwrite=True)
  logging.info('%s is copied.', dest)


def _copy_temp_dir(temp_dir, dest: str):
  """Recursively copies a temporary directory to destination path."""
  logging.info('Copying %s to %s.', temp_dir.name, dest)
  file_utils.recursively_copy_dir(temp_dir.name, dest)
  logging.info('%s is copied.', dest)


def _create_archive(archive_path: str, source_dir: str):
  """Creates an archive file with the contents of the source directory.

  The archive file will be in ZIP format.

  Args:
    archive_path: Path of the archive file to create.
    source_dir: Path of the source directory.
  """
  logging.info('Creating archive %s.', archive_path)
  with tempfile.NamedTemporaryFile() as temp_f:
    with zipfile.ZipFile(temp_f, 'w') as zip_f:
      for dirname, _, filenames in file_utils.walk(source_dir):
        for filename in filenames:
          path = os.path.join(dirname, filename)
          logging.debug('Adding %s to zip file.', path)
          zip_f.write(path, os.path.relpath(path, source_dir))
    _copy_temp_file(temp_f, archive_path)


def _encode_image(im: PIL.Image.Image, **kwargs) -> bytes:
  """Returns the image encoded in the specified format."""
  with io.BytesIO() as output:
    im.save(output, **kwargs)
    return output.getvalue()


def _format_timestamp(timestamp) -> str:
  """Returns the timestamp in human readable format."""
  return timestamp.ToDatetime().isoformat(' ', timespec='seconds')


def _set_fields(pb, keys: Sequence[str], values: Dict[str, Any]):
  """Sets the field of a protocol buffer object.

  Args:
    pb: The protocol buffer object to update.
    keys: List of keys. If a key is present in the values dictionary than the
      corresponding field will be set. Otherwise, the field will be cleared.
    values: a dictionary of values.
  """
  for key in keys:
    value = values.get(key)
    if value:
      setattr(pb, key, value)
    else:
      pb.ClearField(key)


def _is_np_image(obj) -> bool:
  """Returns true if the object is an image represented as a Numpy array."""
  if not isinstance(obj, np.ndarray):
    return False
  shape = obj.shape
  return len(shape) == 3 and shape[-1] == 3


# Numpy objects, which are returned by the environments, e.g. observations, are
# not directly supported by the default JSON encoder. The custom encoder maps
# them and some other objects to supported Python types.
class _CustomJSONEncoder(json.JSONEncoder):
  """Custom JSON encoder."""

  def default(self, obj):
    if isinstance(obj, np.integer):
      return int(obj)
    elif isinstance(obj, np.floating):
      return float(obj)
    elif isinstance(obj, np.bool_):
      return bool(obj)
    elif isinstance(obj, np.ndarray):
      return obj.tolist()
    elif isinstance(obj, bytes):
      return base64.b64encode(obj).decode('utf-8')
    elif isinstance(obj, proto2_message.Message):
      return json.loads(json_format.MessageToJson(obj))
    return json.JSONEncoder.default(self, obj)


def encode_json(data: Any) -> str:
  """Encodes the data in JSON format."""
  # Sort the keys for consistent output, e.g. same order of observations if it
  # is a dictionary.
  return json.dumps(data, cls=_CustomJSONEncoder, sort_keys=True)


class NoCloseWrapper(environment_wrapper.EnvironmentWrapper):
  """Environment wrapper that ignores the close calls."""

  def close(self):
    pass


class EnvironmentHandler(metaclass=abc.ABCMeta):
  """Handles the interactions with an environment."""

  def __init__(self,
               storage: study_storage.Storage,
               user: study_pb2.User,
               config,
               episode_storage_factory: episode_storage.EpisodeStorageFactory,
               base_log_dir: Optional[str],
               log_flush_probability: float = 0.01,
               record_videos: bool = False,
               episode_storage_type: str = 'pickle'):
    """Creates an _EnvironmentEventCallback.

    Args:
      storage: a Storage
      user: a User.
      config: Server config. See config.py.
      episode_storage_factory: Factory to create episode readers and writers.
      base_log_dir: Base directory for storing the episode logs.
      log_flush_probability: Probability to flush the logs after a step.
      record_videos: Enables video recording.
      episode_storage_type: Type of the episode readers and writers. See
        episode_storage_factory.py for the possible options.
    """
    self._storage = storage
    self._user = user
    self._config_json = json.dumps(config)
    self._episode_storage_factory = episode_storage_factory
    self._episode_storage_type = episode_storage_type
    self._base_log_dir = base_log_dir
    self._log_flush_probability = log_flush_probability
    self._record_videos = record_videos

    # Initially there is no study or environment.
    self._session = None
    self._session_path = None
    self._episode = None
    self._run_id = 0
    self._study_spec = None
    self._env_spec = None
    self._env = None
    self._episode_writer = None
    self._video_writer = None
    self._closed = False
    self._replay = None
    self._replay_reader = None
    self._paused = False
    self._episode_index = -1
    self._episode_steps = 0
    self._episode_metadata = None
    # For asynchronous environments, the changes to the environment should be
    # serialized and guarded by this lock.
    self._env_lock = threading.Lock()
    self._fps = constants.ASYNC_FPS
    self._quality = _DEFAULT_QUALITY
    # For asynchronous environments, the timer will be called repeatedly to
    # advance the steps.
    self._timer = None
    self._sync = False
    # Current keys.
    self._keys: environment.Keys = {}
    # Current image. Images are rendered in the _record_step() method and later
    # sent to the client (to avoid rendering them multiple times).
    self._raw_image = None
    self._image = None
    self._pil_image = None
    self.setup()

  def setup(self):
    """Sets up the client."""
    # Send the configuration.
    self._send_config()
    # Send the studies of the user.
    self._set_studies()

  @abc.abstractmethod
  def create_env_from_spec(
      self, env_spec: study_pb2.EnvironmentSpec) -> environment.Environment:
    """Creates an environment based on the specification."""

  @abc.abstractmethod
  def get_url_for_path(self, path: str) -> Optional[str]:
    """Returns the URL to access the specified file or directory.

    Args:
      path: Path of the file or directory.

    Returns:
      a URL or None if it is not possible to have one.
    """

  def create_episode_writer(
      self,
      env: environment.DMEnv,
      path: str,
      metadata: Optional[episode_storage.EnvironmentMetadata] = None
  ) -> episode_storage.EpisodeWriter:
    """Creates an episode writer that stores the data to a directory.

    Args:
      env: a DM environment that will be used to record the episode.
      path: Path of the directory to store the data.
      metadata: Metadata of the environment.

    Returns:
      an EpisodeWriter.
    """
    return self._episode_storage_factory.create_writer(
        self._episode_storage_type, env, path, metadata=metadata)

  def _set_environment(self, env_spec: study_pb2.EnvironmentSpec):
    """Sets the environment based on the spec."""
    self._env = self.create_env_from_spec(env_spec)
    # Changing the environment starts a new run of a sequence of episodes from
    # the chosen environment. Since the session ID is unique, we use a
    # deterministic ID.
    self._run_id += 1
    self._env_spec = env_spec
    self._sync = env_spec.sync
    self._image = None
    self._pil_image = None
    self._episode_index = -1
    self._reset()
    # Send the first frame and metadata about the episode.
    self._send_step()

    self._closed = False
    # Last action time is used to determine whether the user is idle or not.
    self._last_action_time = time.perf_counter()

  def _maybe_save_episode(self):
    """Saves the episode metadata."""
    if not self._episode:
      return
    # Signal end of episode to the writer and close it.
    spec = self._episode_writer.end_episode(self._episode_metadata)
    self._episode_writer.close()
    self._episode_writer = None
    if not self._episode.HasField('state'):
      if not self._episode_steps:
        # Skip the abandoned episodes without any steps.
        logging.info('Ignoring empty abandoned episode.')
        return
      self._episode.state = study_pb2.Episode.STATE_ABANDONED
    # Move the data to its final path. We put ignored episodes under a different
    # directory.
    is_valid = self._episode.state == study_pb2.Episode.STATE_COMPLETED
    final_path = os.path.join(self._session_path, '' if is_valid else 'ignored',
                              self._env_spec.id, self._episode.id)
    # Make sure that the final path exists.
    file_utils.make_dirs(final_path)

    # Update the path in the episode storage spec.
    storage_type = spec.WhichOneof('type')
    if storage_type == 'environment_logger':
      spec.environment_logger.tag_directory = final_path
    if storage_type == 'pickle':
      spec.pickle.path = os.path.join(final_path,
                                      os.path.basename(spec.pickle.path))
    self._episode.storage.CopyFrom(spec)

    self._episode.num_steps = self._episode_steps
    self._episode.total_reward = self._episode_total_reward
    self._episode.end_time.GetCurrentTime()
    threading.Thread(
        target=_copy_temp_dir, args=(self._episode_dir, final_path)).start()
    if self._video_writer:
      # Close the video recorder and copy the file to its proper location.
      self._video_writer.release()
      self._video_writer = None
      filename = os.path.join(final_path, 'video.mp4')
      threading.Thread(
          target=_copy_temp_file, args=(self._video_file, filename)).start()
      self._episode.metadata.update({'video_file': filename})
    logging.info('End of episode %r', self._episode)
    episode = self._get_episode_metadata(self._study_spec, self._env_spec,
                                         self._episode)
    self._send_response(
        save_episode=client_pb2.SaveEpisodeResponse(episode=episode))
    # Save the episode in storage.
    self._storage.create_episode(self._episode)

  def _get_episode_metadata(
      self, study_spec: study_pb2.StudySpec,
      env_spec: study_pb2.EnvironmentSpec,
      episode: study_pb2.Episode) -> client_pb2.EpisodeMetadata:
    """Returns the metadata of the episode."""
    status = study_pb2.Episode.State.Name(episode.state)[6:].capitalize()
    duration = humanize.naturaldelta(episode.end_time.ToSeconds() -
                                     episode.start_time.ToSeconds())
    if 'video_file' in episode.metadata.keys():
      video_url = self.get_url_for_path(episode.metadata['video_file'])
    else:
      video_url = None
    return client_pb2.EpisodeMetadata(
        study=study_spec,
        env=env_spec,
        episode=episode,
        duration=duration,
        video_url=video_url,
        status=status,
        can_delete=utils.can_delete_episode(episode, self._user.email))

  def _record_step(self,
                   timestep: dm_env.TimeStep,
                   action: Optional[Any] = None):
    """Records a step of the current episode and renders its image."""
    # Update the current image. This will be the state after the action is
    # taken.
    self._raw_image, self._image = self._get_image()
    metadata = {
        constants.METADATA_KEYS: self._keys,
        constants.METADATA_IMAGE: self._image
    }
    info = self._env.step_info()
    if info is not None:
      metadata[constants.METADATA_INFO] = info
    self._episode_writer.record_step(
        episode_storage.StepData(timestep, action, metadata))

  def _reset(self):
    """Resets the environment."""
    self._maybe_save_episode()
    # Episode index should be incremented before reset() as it will be added to
    # the episode metadata by the environment writer.
    self._episode_index += 1
    # Create a new episode.
    episode_id = '{}.{}'.format(self._run_id, self._episode_index)
    study_id = self._study_spec.id
    self._episode = study_pb2.Episode(
        id=episode_id,
        study_id=study_id,
        environment_id=self._env_spec.id,
        user=self._user,
        session_id=self._session.id)
    # Add the metadata of the environment.
    self._episode.metadata.update(self._env.metadata())
    self._episode.start_time.GetCurrentTime()
    self._episode_steps = 0
    self._episode_total_reward = 0
    self._episode_metadata = {
        'agent_id': utils.get_agent_id(study_id, self._user.email),
        'episode_id': utils.get_public_episode_id(study_id, episode_id),
        utils.get_metadata_key('env_id'): self._env_spec.id,
        utils.get_metadata_key('study_id'): study_id
    }

    # We log each episode separately. The underlying environment persists.
    self._episode_dir = tempfile.TemporaryDirectory()

    self._episode_writer = self.create_episode_writer(self._env.env(),
                                                      self._episode_dir.name,
                                                      self._episode_metadata)
    # Start the episode and reset the environment.
    self._episode_writer.start_episode()
    self._record_step(self._env.env().reset())

    self._keys = {}
    self._user_input = environment.UserInput(keys=self._keys)

    if self._record_videos:
      self._video_file = tempfile.NamedTemporaryFile(suffix='.mp4')
      raw_image, _ = self._get_image()
      height, width, _ = raw_image.shape
      logging.info('%dx%d video will be recorded to %s.', width, height,
                   self._video_file.name)
      fcc = cv2.VideoWriter_fourcc(*'avc1')
      self._video_writer = cv2.VideoWriter(self._video_file.name, fcc,
                                           self._fps, (width, height))
    # Async environments are put into paused state so that the user can get
    # ready for the next episode.
    self._pause(not self._sync)

  def _get_image(self):
    """Returns the image of the environment in raw and JPEG format."""
    raw_image = self._env.render()
    if self._pil_image and raw_image.flags['C_CONTIGUOUS']:
      # Reuse the existing image. The input image should be C-contiguous. In
      # some environments, e.g. Proco, this may not be the case.
      self._pil_image.frombytes(raw_image)
    else:
      self._pil_image = PIL.Image.fromarray(raw_image)
    return raw_image, _encode_image(
        self._pil_image, format='JPEG', quality=self._quality)

  def _async_step(self):
    """Calls step if environment is active and schedules the next step."""
    with self._env_lock:
      self._timer = None
      if not self._env or self._closed or self._paused:
        # Stop.
        return
      start = time.perf_counter()
      if start - self._last_action_time >= constants.IDLE_TIME_SECS:
        # User was idle. Pause the environment.
        self._pause()
        return

      self._step()
      # Try to match the desired FPS. If the environment is slow, next frame
      # will be rendered immediately.
      elapsed = time.perf_counter() - start
      desired = max(0, (1.0 / self._fps) - elapsed)
      if not self._paused:
        self._timer = threading.Timer(desired, self._async_step)
        self._timer.start()

  def _step(self):
    """Calls step if the environment is not paused and sends the data."""
    if self._paused:
      return
    action = self._env.user_input_to_action(self._user_input)
    if self._sync and action is None:
      return
    timestep = self._env.env().step(action)
    self._record_step(timestep, action)
    self._episode_steps += 1
    self._episode_total_reward += timestep.reward
    self._send_step(timestep.reward)
    # Reset the environment if done.
    if timestep.last():
      self._episode.state = study_pb2.Episode.STATE_COMPLETED
      self._confirm_save()

  def _pause(self, paused=True):
    """Un(pauses) the environment."""
    self._paused = paused
    if not self._sync:
      if not paused:
        self._async_step()
      elif paused and self._timer:
        # async_step() method may be executing, therefore we need to acquire the
        # lock before cancelling the timer.
        with self._env_lock:
          if self._timer:
            logging.info('Cancelling the timer.')
            self._timer.cancel()
    # Inform the user.
    self._send_response(pause=client_pb2.PauseResponse(paused=self._paused))

  def _confirm_save(self):
    """Pauses the environment and asks confirmation to save the episode."""
    self._pause()
    completed = self._episode.state == study_pb2.Episode.STATE_COMPLETED
    self._send_response(
        confirm_save=client_pb2.ConfirmSaveResponse(
            mark_as_completed=completed))

  def _maybe_close_session(self):
    """Closes the current session."""
    if not self._session:
      # Nothing to do.
      return
    self._session.end_time.GetCurrentTime()
    logging.info('End of session %r', self._session)
    if self._env:
      with self._env_lock:
        self._env.env().close()
        self._env = None
    self._maybe_save_episode()
    # Save the updated session metadata, e.g. with end time.
    self._storage.update_session(self._session)
    self._session = None
    self._episode = None

  def _create_new_session(self):
    """Creates a new session and closes the existing one if any."""
    self._maybe_close_session()
    self._session = study_pb2.Session(
        id=uuid.uuid1().hex,
        study_id=self._study_spec.id,
        user=self._user,
        state=study_pb2.Session.State.STATE_VALID)
    self._session.start_time.GetCurrentTime()
    # Create the session directory and store the session metadata.
    self._session_path = os.path.join(self._base_log_dir, self._study_spec.id,
                                      self._session.id)
    file_utils.make_dirs(self._session_path)
    self._storage.create_session(self._session)

  def on_close(self):
    """Called when the interaction is closed."""
    pass

  def close(self):
    """Closes the environment."""
    if self._closed:
      return
    self._closed = True
    self._maybe_close_session()
    self.on_close()

  @abc.abstractmethod
  def send_response(self, response: client_pb2.OperationResponse) -> bool:
    """Sends the response to the client.

    Args:
      response: an OperationResponse.

    Returns:
      True if the response is sent.
    """

  def _send_response(self, **kwargs) -> bool:
    """Builds an operation response and sends it to the client.

    Args:
      **kwargs: Values of the OperationResponse attributes.

    Returns:
      True if the response is sent.
    """
    return self.send_response(client_pb2.OperationResponse(**kwargs))

  def _send_error(self, mesg: str) -> bool:
    """Sends the error message to the client."""
    return self._send_response(error=client_pb2.ErrorResponse(mesg=mesg))

  def _send_config(self) -> bool:
    """Sends the config to the client."""
    return self._send_response(
        config=client_pb2.ConfigResponse(config=self._config_json))

  def _set_studies(self):
    """Called to get the studies of the user."""
    studies = self._storage.get_studies(email=self._user.email)
    self._send_response(
        set_studies=client_pb2.SetStudiesResponse(studies=studies))

  def _select_study(self, study_id: str):
    """Called when the user selects a study."""
    study_spec = self._storage.get_study(study_id)
    if not study_spec:
      self._send_error('Missing study.')
      return
    if not utils.can_access_study(study_spec, self._user.email):
      self._send_error('You cannot access this study.')
      return
    self._study_spec = study_spec
    # Changing the study starts a new session.
    self._create_new_session()
    self._send_response(
        select_study=client_pb2.SelectStudyResponse(study=study_spec))
    # We send existing episodes for the study separately to reduce latency for
    # the player.
    # TODO(sertan): Add paging.
    self._send_episodes()

  def _save_study(self, study_spec: study_pb2.StudySpec) -> bool:
    """Called to save a study.

    Args:
      study_spec: Study specification.

    Returns:
      True if the response is sent to the client.
    """
    study_id = study_spec.id
    if study_id:
      # Load the existing study and check that the user can modify it.
      existing_study_spec = self._storage.get_study(study_id)
      if not existing_study_spec:
        return self._send_error('Missing study.')
      if not utils.can_update_study(existing_study_spec, self._user.email):
        return self._send_error('You cannot modify this study.')
      # Copy the readonly fields.
      study_spec.creator.CopyFrom(existing_study_spec.creator)
      study_spec.creation_time.CopyFrom(existing_study_spec.creation_time)
      study_spec.state = existing_study_spec.state
    else:
      study_spec.creator.email = self._user.email

    try:
      # Validate the study specification.
      utils.validate_study_spec(study_spec)
      if study_id:
        self._storage.update_study(study_spec)
      else:
        self._storage.create_study(study_spec)
    except ValueError as e:
      return self._send_error(str(e))
    self._send_response(save_study=client_pb2.SaveStudyResponse())

  def _enable_study(self, study_id: str, enable: bool) -> bool:
    """Called to enable / disable a study.

    Args:
      study_id: ID of the study.
      enable: Whether to enable or disable the study.

    Returns:
      True if the response is sent to the client.
    """
    # Check that the study exists and the user can modify it.
    study_spec = self._storage.get_study(study_id)
    if not study_spec:
      return self._send_error('Missing study.')
    if not utils.can_update_study(study_spec, self._user.email):
      return self._send_error('You cannot modify this study.')
    self._storage.update_study_state(
        study_id, study_pb2.StudySpec.STATE_ENABLED
        if enable else study_pb2.StudySpec.STATE_DISABLED)
    return self._send_response(
        enable_study=client_pb2.EnableStudyResponse(
            study_id=study_id, enabled=enable))

  def _select_environment(self, env_id: str):
    """Called when the user select an environment."""
    # Reset the current environment, if any.
    if self._env:
      with self._env_lock:
        self._reset()
    if not self._study_spec:
      self._send_error('No study is selected.')
      return
    self._env_spec = utils.get_env_spec_by_id(self._study_spec, env_id)
    if not self._env_spec:
      self._send_error('Missing environment.')
      return
    self._set_environment(self._env_spec)
    # We send the environment response at the end. This ensures that the client
    # will display the busy overlay until the environment is created and the
    # initial image is sent.
    self._send_response(
        select_environment=client_pb2.SelectEnvironmentResponse(
            study_id=self._study_spec.id, env=self._env_spec))

  def _send_step(self, reward=0):
    """Sends the step data to the client."""
    self._send_response(
        step=client_pb2.StepResponse(
            image=self._image,
            episode_index=self._episode_index + 1,
            episode_steps=self._episode_steps,
            reward=reward))
    # Also add frame to the video. CV2 expects the image in BGR channel order.
    if self._video_writer:
      self._video_writer.write(cv2.cvtColor(self._raw_image, cv2.COLOR_RGB2BGR))

  def _send_episodes(self):
    """Sends the metadata of the episodes of the user for the current study."""
    email = self._user.email
    if self._study_spec.creator.email == email:
      # Allow the study owner to see all episodes.
      email = None
    episodes = self._storage.get_episodes(self._study_spec.id, email=email)
    logging.info('Loaded %d episode(s) for %s in study %s.', len(episodes),
                 self._user.email, self._study_spec.id)
    episodes_response = client_pb2.EpisodesResponse()
    for episode in episodes:
      # The episodes are from the current study and therefore the environment
      # specs should be present.
      env_spec = utils.get_env_spec_by_id(self._study_spec,
                                          episode.environment_id)
      if not env_spec:
        continue
      episodes_response.episodes.append(
          self._get_episode_metadata(self._study_spec, env_spec, episode))
    # The response will be empty if there are no existing episodes.
    self._send_response(episodes=episodes_response)

  def _delete_episode(self, request: client_pb2.DeleteEpisodeRequest):
    """Called to delete an episode."""
    ref = request.ref
    episode = self._storage.get_episode(ref.study_id, ref.session_id,
                                        ref.episode_id)
    if not episode:
      self._send_error('Missing episode.')
      return
    if not utils.can_delete_episode(episode, self._user.email):
      self._send_error('You cannot delete this episode.')
      return
    success = self._storage.delete_episode(ref.study_id, ref.session_id,
                                           ref.episode_id)
    if success:
      try:
        utils.delete_episode_storage(episode)
      except Exception:
        # Deleting the episode files is best-effort.
        logging.exception('Unable to delete episode files.')
    self._send_response(
        delete_episode=client_pb2.DeleteEpisodeResponse(
            ref=ref, success=success))

  def _replay_episode(self, study_id: str, session_id: str,
                      episode_id: str) -> None:
    """Initializes the specified episode for replay and sends its metadata.

    Args:
      study_id: ID of the study.
      session_id: ID of the session.
      episode_id: ID of the episode.
    """
    if study_id == 'file.pickle':
      path = os.path.join(session_id, episode_id)
      self._replay_reader = self._episode_storage_factory.create_reader(
          study_pb2.Episode.Storage(
              pickle=study_pb2.Episode.Storage.Pickle(path=path)))
      self._replay = replay.StaticReplay(
          self._replay_reader.steps,
          session_id=session_id,
          episode_id=episode_id)
    if study_id == 'file':
      self._replay_reader = self._episode_storage_factory.create_reader(
          study_pb2.Episode.Storage(
              environment_logger=study_pb2.Episode.Storage.EnvironmentLogger(
                  tag_directory=session_id, index=int(episode_id))))
      self._replay = replay.StaticReplay(
          self._replay_reader.steps,
          session_id=session_id,
          episode_id=episode_id)
    else:
      self._replay_reader = None
      self._replay = replay.StorageReplay(self._episode_storage_factory,
                                          self._storage, study_id, session_id,
                                          episode_id)
    episode = self._replay.episode
    episode_metadata = self._get_episode_metadata(self._replay.study_spec,
                                                  self._replay.env_spec,
                                                  episode)
    # Collect step rewards. Some values may be None, e.g. for the first step, we
    # replace them by 0.
    step_rewards = []
    for i in range(episode.num_steps + 1):  # Include the final reward.
      step = self._replay.get_step(i)
      step_rewards.append(step.timestep.reward
                          if step and step.timestep.reward is not None else 0)
    self._send_response(
        replay_episode=client_pb2.ReplayEpisodeResponse(
            episode=episode_metadata, step_rewards=step_rewards))

  def _send_replay_step(self, index: int) -> None:
    """Sends the data for the specified step of the current replay.

    Args:
      index: Index of the step in [0, num_steps).
    """
    if not self._replay:
      return
    step = self._replay.get_step(index)
    if not step:
      return
    obs = step.timestep.observation
    # Send the compressed image for image like observations. This is more
    # efficient than doing the rendering on the client side. We use a lossless
    # format.
    observation = client_pb2.Data()
    if _is_np_image(obs):
      # No name.
      observation.images.add().image = _encode_image(
          PIL.Image.fromarray(obs), format='PNG')
    else:
      if isinstance(obs, dict):
        # Extract the image observations and send them as images.
        non_image_obs = {}
        for key, value in obs.items():
          if _is_np_image(value):
            image = observation.images.add()
            image.name = key
            image.image = _encode_image(
                PIL.Image.fromarray(value), format='PNG')
          else:
            non_image_obs[key] = value
        if non_image_obs:
          observation.json_encoded = encode_json(non_image_obs)
      else:
        observation.json_encoded = encode_json(obs)
    action = client_pb2.Data(json_encoded=encode_json(step.action))
    # Get the tags from the step metadata, if any.
    tags = []
    step_metadata = self._replay.episode.step_metadata
    if index in step_metadata:
      tags = [tag.label for tag in step_metadata[index].tags]
    self._send_response(
        replay_step=client_pb2.ReplayStepResponse(
            index=index,
            image=step.custom_data.get(constants.METADATA_IMAGE),
            keys=step.custom_data.get(constants.METADATA_KEYS),
            reward=step.timestep.reward,
            observation=observation,
            action=action,
            tags=tags))

  def _add_episode_tag(self, tag: str) -> None:
    """Adds a tag to the episode being replayed.

    Args:
      tag: Label of the tag.
    """
    success = self._replay is not None and self._replay.add_episode_tag(tag)
    self._send_response(
        add_episode_tag=client_pb2.AddEpisodeTagResponse(
            tag=tag, success=success))

  def _remove_episode_tag(self, tag: str) -> None:
    """Removes the tag from the episode being replayed.

    Args:
      tag: Label of the tag.
    """
    success = self._replay is not None and self._replay.remove_episode_tag(tag)
    self._send_response(
        remove_episode_tag=client_pb2.RemoveEpisodeTagResponse(
            tag=tag, success=success))

  def _update_replay_episode(self, notes: str) -> None:
    """Updates the metadata of the episode being replayed.

    Args:
      notes: Episode notes.
    """
    success = self._replay is not None and self._replay.update_episode(notes)
    self._send_response(
        update_replay_episode=client_pb2.UpdateReplayEpisodeResponse(
            success=success))

  def _add_step_tag(self, request: client_pb2.AddStepTagRequest) -> None:
    """Adds a tag to a step of the episode being replayed."""
    success = (
        self._replay is not None and
        self._replay.add_step_tag(request.index, request.tag))
    self._send_response(
        add_step_tag=client_pb2.AddStepTagResponse(
            index=request.index, tag=request.tag, success=success))

  def _remove_step_tag(self, request: client_pb2.RemoveStepTagRequest) -> None:
    """Removes the tag from a step of the episode being replayed."""
    success = (
        self._replay is not None and
        self._replay.remove_step_tag(request.index, request.tag))
    self._send_response(
        remove_step_tag=client_pb2.RemoveStepTagResponse(
            index=request.index, tag=request.tag, success=success))

  def _download_episodes(self, request: client_pb2.DownloadEpisodesRequest):
    """Merges a set of episodes in a downloadable form."""
    study_id = None
    environment_id = None
    episodes = []
    for ref in request.refs:
      if study_id is None:
        study_id = ref.study_id
      elif ref.study_id != study_id:
        raise ValueError('Episodes are not from the same study.')
      episode = self._storage.get_episode(ref.study_id, ref.session_id,
                                          ref.episode_id)
      if not episode:
        raise ValueError('One of the episodes is missing.')
      if environment_id is None:
        environment_id = episode.environment_id
      elif episode.environment_id != environment_id:
        raise ValueError('Episodes must be from the same environment.')
      episodes.append(episode)

    # Merge the episodes.
    env = merger.Merger(
        episodes,
        self._episode_storage_factory,
        strip_internal_metadata=request.strip_internal_metadata,
        end_of_episode_tags=request.end_of_episode_tags,
        add_step_tags_as_metadata=True,
        num_preloaded_episodes=MERGER_NUM_PRELOADED_EPISODES)
    # Make sure that the archive directory exists.
    download_dir = os.path.join(self._base_log_dir, 'download')
    file_utils.make_dirs(download_dir)
    download_id = uuid.uuid1().hex
    if request.archive:
      # We create the archive file locally under a temporary directory.
      temp_tag_dir = tempfile.TemporaryDirectory()
      tag_dir = temp_tag_dir.name
    else:
      tag_dir = os.path.join(download_dir, download_id)

    # TODO(sertan): With episode read and writers, merger no longer needs to be
    # an environment wrapper. It will simplify the logic here.
    writer = self.create_episode_writer(env, tag_dir)
    episode_metadata = None

    def start_episode():
      nonlocal episode_metadata
      writer.start_episode()
      timestep = env.reset()
      episode_metadata = env.episode_metadata_fn(timestep, None, env)
      writer.record_step(
          episode_storage.StepData(timestep, None,
                                   env.step_fn(timestep, None, env)))

    start_episode()
    num_episodes = len(episodes)
    processed_episodes = 0
    while not env.done:
      action = env.next_action()
      timestep = env.step(action)
      writer.record_step(
          episode_storage.StepData(timestep, action,
                                   env.step_fn(timestep, action, env)))
      episode_metadata = (
          env.episode_metadata_fn(timestep, action, env) or episode_metadata)
      if timestep.last():
        writer.end_episode(episode_metadata)
        if not env.done:
          start_episode()
          processed_episodes += 1
          # Update the progress.
          progress = 100.0 * processed_episodes / num_episodes
          self._send_response(
              download_episodes=client_pb2.DownloadEpisodesResponse(
                  progress=progress))

    writer.close()

    if request.archive:
      archive_path = os.path.join(download_dir, f'{download_id}.zip')
      _create_archive(archive_path, temp_tag_dir.name)
      url = self.get_url_for_path(archive_path)
    else:
      url = self.get_url_for_path(tag_dir)
    self._send_response(
        download_episodes=client_pb2.DownloadEpisodesResponse(
            url=url, progress=100))

  def _handle_action(self, request: client_pb2.ActionRequest):
    """Handles the user action."""
    keys = {_KEY_MAPPING.get(key, key): 1 for key in request.keys}
    # Convert gamepad input into (virtual) keys.
    for index, button in request.gamepad_input.buttons.items():
      # We ignore the touched state. Value will be 1.0 for digital buttons when
      # pressed. Values of analog buttons will be in range (0, 1.0].
      keys[f'Button{index}'] = button.value
    for index, value in request.gamepad_input.axes.items():
      keys[f'Axis{index}'] = value
    self._last_action_time = time.perf_counter()
    if self._sync and not keys:
      # This indicates that all keys are released. It is ignored in sync mode.
      return
    # Update the current keys and map them to an environment action.
    self._keys = keys
    controller_id = request.gamepad_input.id
    # In theory, the user can change the controllers during an episode. But the
    # client will use only one of them. We keep the current ID if the controller
    # was active.
    if (controller_id and
        (request.gamepad_input.buttons or request.gamepad_input.axes)):
      self._episode.controller_id = controller_id
    controller = (
        environment.Controller.SPACEMOUSE
        if 'SpaceMouse' in controller_id else environment.Controller.DEFAULT)
    # In asynchronous environment, the controller can be stateful. Therefore, we
    # don't conver the user input to environment action here, but rather in the
    # _step() method.
    self._user_input = environment.UserInput(
        keys=self._keys, controller=controller)
    env_type = (
        EnvType(self._env_spec.WhichOneof('type')) if self._env_spec else None)
    is_procgen = env_type == EnvType.PROCGEN
    if PAUSE_KEY in self._keys:
      self._pause(not self._paused)
    elif 'Return' in self._keys and not is_procgen:
      # Procgen doesn't support explicit resets and handle the return key
      # itself.
      self._episode.state = study_pb2.Episode.STATE_CANCELLED
      self._confirm_save()
    elif self._sync:
      self._step()

  def _set_camera(self, request: client_pb2.SetCameraRequest):
    """Sets the camera used for rendering images."""
    if not self._env:
      # The client will not wait for a response.
      return
    camera_info = self._env.set_camera(request.index)
    if not camera_info:
      return
    self._send_response(
        set_camera=client_pb2.SetCameraResponse(
            index=camera_info.index, name=camera_info.name))
    if self._paused or self._sync:
      # Update the image if the environment is paused or in sync mode. The
      # reward will be 0, but this is a cosmetic issue. In async mode, it will
      # be updated with the next step.
      _, self._image = self._get_image()
      self._send_response(
          step=client_pb2.StepResponse(
              image=self._image,
              episode_index=self._episode_index + 1,
              episode_steps=self._episode_steps))

  def handle_request(self, request: client_pb2.OperationRequest):
    """Handles the operation request."""
    try:
      self._handle_request(request)
    except Exception as e:
      logging.exception('Request failed.')
      self._send_error(f'Request failed: {e}')

  def _handle_request(self, request: client_pb2.OperationRequest):
    """Handles the request received from the client."""
    op = request.WhichOneof('type')
    if op == 'set_studies':
      self._set_studies()
    elif op == 'select_study':
      self._select_study(request.select_study.study_id)
    elif op == 'save_study':
      self._save_study(request.save_study.study)
    elif op == 'enable_study':
      self._enable_study(request.enable_study.study_id,
                         request.enable_study.enable)
    elif op == 'select_environment':
      self._select_environment(request.select_environment.env_id)
    elif op == 'save_episode':
      save_episode = request.save_episode
      if not save_episode.accept:
        self._episode.state = study_pb2.Episode.STATE_REJECTED
      elif save_episode.mark_as_completed:
        self._episode.state = study_pb2.Episode.STATE_COMPLETED
      else:
        self._episode.state = study_pb2.Episode.STATE_CANCELLED
      # Environment will be in paused state and we don't need locking.
      self._reset()
      self._send_step()
    elif op == 'delete_episode':
      self._delete_episode(request.delete_episode)
    elif op == 'set_camera':
      self._set_camera(request.set_camera)
    elif op == 'set_fps':
      self._fps = request.set_fps.fps
    elif op == 'set_quality':
      self._quality = _QUALITY_MAPPING.get(request.set_quality.quality,
                                           _DEFAULT_QUALITY)
    elif op == 'action' and self._env:
      self._handle_action(request.action)
    elif op == 'replay_episode':
      ref = request.replay_episode.ref
      self._replay_episode(ref.study_id, ref.session_id, ref.episode_id)
    elif op == 'replay_step':
      self._send_replay_step(request.replay_step.index)
    elif op == 'add_episode_tag':
      self._add_episode_tag(request.add_episode_tag.tag)
    elif op == 'remove_episode_tag':
      self._remove_episode_tag(request.remove_episode_tag.tag)
    elif op == 'update_replay_episode':
      self._update_replay_episode(request.update_replay_episode.notes)
    elif op == 'add_step_tag':
      self._add_step_tag(request.add_step_tag)
    elif op == 'remove_step_tag':
      self._remove_step_tag(request.remove_step_tag)
    elif op == 'download_episodes':
      self._download_episodes(request.download_episodes)
