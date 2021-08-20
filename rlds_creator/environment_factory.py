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

"""Environment factory."""

from rlds_creator import environment
from rlds_creator import environment_proxy
from rlds_creator import study_pb2
from rlds_creator.envs import atari_env
from rlds_creator.envs import dmlab_env
from rlds_creator.envs import net_hack_env
from rlds_creator.envs import procgen_env
from rlds_creator.envs import robodesk_env
from rlds_creator.envs import robosuite_env


def _create_local_env_from_spec(
    env_spec: study_pb2.EnvironmentSpec) -> environment.Environment:
  """Returns an environment based on the specification."""
  env_type = env_spec.WhichOneof('type')
  if env_type == 'procgen':
    return procgen_env.ProcgenEnvironment(env_spec)
  elif env_type == 'atari':
    return atari_env.AtariEnvironment(env_spec)
  elif env_type == 'dmlab':
    return dmlab_env.DmLabEnvironment(env_spec)
  elif env_type == 'net_hack':
    return net_hack_env.NetHackEnvironment(env_spec)
  elif env_type == 'robodesk':
    return robodesk_env.RoboDeskEnvironment(env_spec)
  elif env_type == 'robosuite':
    return robosuite_env.RobosuiteEnvironment(env_spec)
  else:
    raise ValueError('Unsupported environment spec.')


def create_env_from_spec(
    env_spec: study_pb2.EnvironmentSpec) -> environment.Environment:
  """Returns the environment based on the specification."""
  env_type = env_spec.WhichOneof('type')
  if env_type in ['net_hack', 'robosuite']:
    # Robosuite uses mujoco_py which has a rendering bug due to multithreading.
    # The first (and some of the later) steps are rendered properly and others
    # are simply black images. We run Robosuite environments in a separate
    # process to overcome this issue.
    #
    # NetHack is not thread-safe.
    return environment_proxy.create_proxied_env_from_spec(
        env_spec, _create_local_env_from_spec)
  return _create_local_env_from_spec(env_spec)
