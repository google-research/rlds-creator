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

"""Utilities."""

import hashlib
from typing import Iterable, Optional

from rlds_creator import constants
from rlds_creator import file_utils
from rlds_creator import study_pb2


def get_env_spec_by_id(study_spec: study_pb2.StudySpec,
                       env_id: str) -> Optional[study_pb2.EnvironmentSpec]:
  """Returns the spec of the environment with the specified ID."""
  for env_spec in study_spec.environment_specs:
    if env_spec.id == env_id:
      return env_spec
  return None


def validate_study_spec(study_spec: study_pb2.StudySpec):
  """Checks that the study specification is valid."""
  # Creator email should be set.
  if not study_spec.creator.email:
    raise ValueError('Creator email should be set.')
  if not study_spec.environment_specs:
    raise ValueError('No environment specified.')
  # Environment specifications should be valid.
  for env_spec in study_spec.environment_specs:
    if not env_spec.id:
      raise ValueError('Environment ID is missing.')


def can_access_study(study_spec: study_pb2.StudySpec, email: str) -> bool:
  """Returns true if the user can access the study."""
  return (study_spec.creator.email == email or
          study_spec.state == study_pb2.StudySpec.STATE_ENABLED)


def can_update_study(study_spec: study_pb2.StudySpec, email: str) -> bool:
  """Returns true if the user can update the study."""
  return study_spec.creator.email == email


def can_delete_episode(episode: study_pb2.Episode, email: str) -> bool:
  """Returns true of the user can delete the episode."""
  # Only the user that created the episode can delete it.
  # TODO(sertan): We may also allow the study owner to delete them.
  return episode.user.email == email


def delete_episode_storage(episode: study_pb2.Episode):
  """Deletes the stored files for the episode."""
  storage = episode.storage
  if storage.environment_logger.tag_directory:
    file_utils.delete_recursively(storage.environment_logger.tag_directory)
  if storage.pickle.path:
    file_utils.delete_recursively(storage.pickle.path)


def hash_strings(items: Iterable[str]) -> str:
  """Hashes the specified strings."""
  # Salts, e.g. in blake2s, have fixed length, which is not the case for email
  # and study ID, so we merge them and hash instead of an explicit salt.
  return hashlib.sha256(str.encode('#'.join(items))).hexdigest()


def get_agent_id(study_id: str, email: str) -> str:
  """Returns the (hashed) agent ID based on the study ID and email.

  The agent ID will be consistent for the same email address within a study. It
  may differ from one study to another.

  Args:
    study_id: ID of the study.
    email: Email of the user.

  Returns:
    A (likely) unique agent ID for the study ID and email pair.
  """
  return hash_strings((email, study_id))


def get_metadata_key(name: str) -> str:
  """Returns the namespaced key for the specified metadata field."""
  return constants.METADATA_NAMESPACE + name


def get_public_episode_id(study_id: str, episode_id: str) -> str:
  """Returns the public episode ID which will likely to be unique.

  The public episode ID will be a hash of the the study ID and episode ID.

  Args:
    study_id: ID of the study.
    episode_id: ID of the episode.

  Returns:
    A (likely) unique episode ID.
  """
  return hash_strings((study_id, episode_id))
