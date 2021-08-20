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

"""Utilities for unit tests."""

from typing import Any, List, Optional, Tuple

from rlds_creator import environment
from rlds_creator import episode_storage
from rlds_creator import pickle_episode_storage
from rlds_creator import study_pb2
from rlds_creator import utils
from rlds_creator.envs import procgen_env

# Default number of maximum steps in the test environments.
MAX_EPISODE_STEPS = 100
STUDY_ID = 'study'
USER_EMAIL = 'user@test.com'
# Agent ID for the study ID and user email above.
AGENT_ID = '8ed1a0d61d92bf1cc932786eac3b9680d2426a947aa94b8f850283c7b9976947'


def create_env(
    env_id: str,
    max_episode_steps: int = MAX_EPISODE_STEPS
) -> procgen_env.ProcgenEnvironment:
  """Creates a Procgen environment with the specified ID."""
  return procgen_env.ProcgenEnvironment(
      study_pb2.EnvironmentSpec(
          max_episode_steps=max_episode_steps,
          procgen=study_pb2.EnvironmentSpec.Procgen(id=env_id, rand_seed=0)))


def record_episode(
    writer: episode_storage.EpisodeWriter,
    episode_id: str,
    env_id: str,
    env: environment.Environment,
    step_fn=None,
    episode_metadata: Optional[episode_storage.EpisodeMetadata] = None,
    study_id: str = STUDY_ID,
    session_id: str = 'session',
    user_email: str = USER_EMAIL,
) -> Tuple[study_pb2.Episode, List[environment.TimeStep], List[Any]]:
  """Records an episode of the environment.

  Args:
    writer: an EpisodeWriter.
    episode_id: ID of the episode.
    env_id: ID of the environment.
    env: an Environment.
    step_fn: Called at each step to obtain the custom step data.
    episode_metadata: Episode metadata.
    study_id: ID of the study.
    session_id: ID of the session.
    user_email: Email of the user.

  Returns:
    a tuple of Episode object with episode metadata, list of timesteps and
    list of actions in the episode.
  """
  writer.start_episode()

  def custom_data():
    data = step_fn() if step_fn else {}
    # Add the image keys to custom data if not present.
    if 'image' not in data:
      data['image'] = env.render()
    if 'keys' not in data:
      data['keys'] = None
    return data

  denv = env.env()
  timestep = denv.reset()
  writer.record_step(episode_storage.StepData(timestep, None, custom_data()))
  timesteps = [timestep]
  num_steps = 0
  total_reward = 0.0
  actions = []
  action_spec = denv.action_spec()
  while not timestep.last():
    action = action_spec.generate_value()
    actions.append(action)
    timestep = denv.step(action)
    writer.record_step(
        episode_storage.StepData(timestep, action, custom_data()))
    timesteps.append(timestep)
    num_steps += 1
    total_reward += timestep.reward
  episode_metadata = episode_metadata or {}
  episode_metadata.update({
      'agent_id': utils.get_agent_id(study_id, user_email),
      'episode_id': episode_id,
      utils.get_metadata_key('env_id'): env_id,
      utils.get_metadata_key('study_id'): study_id,
  })
  storage_spec = writer.end_episode(episode_metadata)
  episode = study_pb2.Episode(
      id=episode_id,
      study_id=study_id,
      environment_id=env_id,
      user=study_pb2.User(email=user_email),
      session_id=session_id,
      state=study_pb2.Episode.STATE_COMPLETED,
      num_steps=num_steps,
      total_reward=total_reward,
      storage=storage_spec)
  return episode, timesteps, actions


def record_single_episode(
    episode_id: str,
    env_id: str,
    root_directory: str,
    max_episode_steps: int = MAX_EPISODE_STEPS,
    **kwargs
) -> Tuple[study_pb2.Episode, List[environment.TimeStep], List[Any]]:
  """Creates an environment and records a single episode.

  Args:
    episode_id: ID of the episode.
    env_id: ID of the environment.
    root_directory: Path of the directory to store the episode using the Pickle
      episode writer.
    max_episode_steps: Maximum number of steps in the episode.
    **kwargs: Arguments that are passed to record_episode() method.

  Returns:
    See record_episode() method.
  """
  env = create_env(env_id, max_episode_steps=max_episode_steps)
  writer = pickle_episode_storage.PickleEpisodeWriter(env.env(), root_directory)
  output = record_episode(writer, episode_id, env_id, env, **kwargs)
  writer.close()
  return output
