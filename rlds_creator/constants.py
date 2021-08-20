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

"""Constants."""

import enum

# For async environments, we pause the environment if there is no human action
# after this many seconds.
IDLE_TIME_SECS = 6.0

# Frames per second for the asynchronous mode.
ASYNC_FPS = 15.0

# Namespace for application specific metadata.
METADATA_NAMESPACE = 'rlds_creator:'

# Keys of the fields that may be present in the step metadata.
METADATA_IMAGE = 'image'
METADATA_INFO = 'info'
METADATA_KEYS = 'keys'


class EnvType(enum.Enum):
  """Supported environment types. See EnvironmentSpec in study.proto."""
  ATARI = 'atari'
  DMLAB = 'dmlab'
  NET_HACK = 'net_hack'
  PROCGEN = 'procgen'
  ROBODESK = 'robodesk'
  ROBOSUITE = 'robosuite'
