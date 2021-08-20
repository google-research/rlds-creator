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

"""Storage layer for RLDS Creator."""

import abc
from typing import Callable, List, Optional

from rlds_creator import study_pb2


class Storage(metaclass=abc.ABCMeta):
  """RLDS Creator storage."""

  @abc.abstractmethod
  def create_study(self, study_spec: study_pb2.StudySpec) -> str:
    """Creates a study with the provided specification and returns its ID."""

  @abc.abstractmethod
  def get_study(self, study_id: str) -> Optional[study_pb2.StudySpec]:
    """Returns the study with the specified ID.

    Args:
      study_id: ID of the study.

    Returns:
      a StudySpec or None if such a study does not exist.
    """

  @abc.abstractmethod
  def update_study_state(self, study_id: str, state: study_pb2.StudySpec.State):
    """Updates the state of the study with the specified ID.

    Args:
      study_id: ID of the study.
      state: New state of the study.

    Raises:
      ValueError if the study is missing.
    """

  @abc.abstractmethod
  def update_study(self, study_spec: study_pb2.StudySpec):
    """Updates the study.

    Args:
      study_spec: A StudySpec. The id field should be set and point to an
        existing study. The creation_time and state fields will be ignored.

    Raises:
      ValueError if the study is missing.
    """

  @abc.abstractmethod
  def get_studies(self,
                  state: Optional['study_pb2.StudySpec.State'] = None,
                  email: Optional[str] = None) -> List[study_pb2.StudySpec]:
    """Returns the list of studies matching the specified constraints.

    Args:
      state: State of the study.
      email: Email of the user who created the study.

    Returns:
      a list of StudySpecs.
    """

  @abc.abstractmethod
  def create_session(self, session: study_pb2.Session) -> None:
    """Creates the session for a study.

    Args:
      session: a Session. The study_id, id and start_time fields should be set.
        The corresponding study should exist.

    Raises:
      ValueError if the session is not valid or the study of the session is
      missing.
    """

  @abc.abstractmethod
  def update_session(self, session: study_pb2.Session) -> None:
    """Updates an existing session for a study.

    Args:
      session: a Session. The study_id, id and start_time fields should be set.
        The corresponding study and session should exist.

    Raises:
      ValueError if the session is not valid or the session is missing.
    """

  @abc.abstractmethod
  def get_session(self, study_id: str,
                  session_id: str) -> Optional[study_pb2.Session]:
    """Returns the session with the specified ID for the study.

    Args:
      study_id: ID of the study.
      session_id: ID of the session.

    Returns:
      a Session or None if such a session or study does not exist.
    """

  @abc.abstractmethod
  def create_episode(self, episode: study_pb2.Episode) -> None:
    """Creates the episode for a session in a study.

    Args:
      episode: an Episode. The study_id, session_id, id and start_time fields
        should be set. The corresponding study and session should exist.

    Raises:
      ValueError if the study of the episode is missing.
    """

  @abc.abstractmethod
  def get_episode(self, study_id: str, session_id: str,
                  episode_id: str) -> Optional[study_pb2.Episode]:
    """Returns the episode with the specified ID for the session in a study.

    Args:
      study_id: ID of the study.
      session_id: ID of the session.
      episode_id: ID of the episode.

    Returns:
      an Episode or None if such a {study, session, episode} does not exist.
    """

  @abc.abstractmethod
  def atomic_update_episode(
      self, study_id: str, session_id: str, episode_id: str,
      callback: Callable[[study_pb2.Episode], bool]) -> bool:
    """Atomically updates an episode in a transaction.

    Args:
      study_id: ID of the study.
      session_id: ID of the session.
      episode_id: ID of the episode.
      callback: Callback function that will be called with the read episode. It
        should update the episode object and return true to save it, or false to
        cancel the update. Study, session and episode IDs cannot be modified.

    Returns:
      True if the episode is updated successfully.

    Raises:
      ValueError if the study, session or episode ID of the updated episode is
      different from the existing values.
    """

  @abc.abstractmethod
  def get_episodes(self,
                   study_id: str,
                   email: Optional[str] = None) -> List[study_pb2.Episode]:
    """Returns the list of episodes matching the specified constraints.

    The default ordering will be in decreasing creation timestamp.

    Args:
      study_id: ID of the study.
      email: email of the user who recorded the episodes.

    Returns:
      a list of Episodes.
    """

  @abc.abstractmethod
  def delete_episode(self, study_id: str, session_id: str,
                     episode_id: str) -> bool:
    """Deletes an episode.

    This will be a n-op if the episode does not exist.

    Args:
      study_id: ID of the study.
      session_id: ID of the session.
      episode_id: ID of the episode.

    Returns:
      True on success.
    """


def validate_session(session: study_pb2.Session) -> None:
  """Validates a session for creation and update.

  Args:
    session: Session to validate.

  Raises:
    ValueError if the session is invalid with a message indicating the reason.
  """
  if not session.study_id:
    raise ValueError('Study ID should be set.')
  if not session.id:
    raise ValueError('Session ID should be set.')
  if not session.HasField('start_time'):
    raise ValueError('Start time should be set.')


def validate_episode(episode: study_pb2.Episode) -> None:
  """Validates an episode for creation.

  Args:
    episode: Episode to validate.

  Raises:
    ValueError if the episode is invalid with a message indicating the reason.
  """
  if not episode.study_id:
    raise ValueError('Study ID should be set.')
  if not episode.session_id:
    raise ValueError('Session ID should be set.')
  if not episode.id:
    raise ValueError('Episode ID should be set.')
  if not episode.HasField('start_time'):
    raise ValueError('Start time should be set.')
