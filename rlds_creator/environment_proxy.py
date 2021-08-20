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

"""Proxied environment that runs in a separate process."""

import enum
import multiprocessing
import multiprocessing.connection
import threading
from typing import Callable, Optional

from absl import logging
import dm_env
from rlds_creator import environment
from rlds_creator import study_pb2

# Timeout for receiving data in the environment proxy.
PROXY_RECV_TIMEOUT_SECS = 60
# Timeout for terminating the child process of the environment proxy.
PROXY_TERMINATION_TIMEOUT_SECS = 10


class Cmd(enum.Enum):
  """Environment proxy commands."""
  # environment.Environment methods.
  KEYS_TO_ACTION = 1
  USER_INPUT_TO_ACTION = 11
  RENDER = 2
  SET_CAMERA = 12
  METADATA = 3
  # dm_env.Environment methods.
  RESET = 4
  STEP = 5
  OBSERVATION_SPEC = 6
  ACTION_SPEC = 7
  CLOSE = 8
  # Used internally.
  INIT = 9
  QUIT = 10


class EnvironmentProxy(environment.Environment, dm_env.Environment):
  """Proxy environment.

  This class implements both environment.Environment and DM Environment
  interfaces and sends the method invocations to the handler that executes them
  in a separate process.
  """

  def __init__(self, conn: multiprocessing.connection.Connection,
               process: multiprocessing.Process):
    self._conn = conn
    self._process = process
    # Used to serialize the method invocations.
    self._lock = threading.Lock()
    self._send(Cmd.INIT)

  def _send(self, cmd: Cmd, args=None):
    """Sends the command to the child process and returns the response."""
    with self._lock:
      logging.debug('Sending command %s', cmd)
      # Exceptions raised in send and recv calls will be handled upstream.
      self._conn.send([cmd, args])
      if not self._conn.poll(PROXY_RECV_TIMEOUT_SECS):
        raise IOError('Environment proxy timed-out.')
      resp = self._conn.recv()
      if isinstance(resp, Exception):
        raise resp
      return resp

  def __del__(self):
    # Signal termination to the child process and wait for some time.
    try:
      self._send(Cmd.QUIT)
    finally:
      self._conn.close()
    self._process.join(PROXY_TERMINATION_TIMEOUT_SECS)
    # Force termination if still running.
    if self._process.exitcode is None:
      self._process.terminate()

  # environment.Environment methods.

  def env(self) -> dm_env.Environment:
    return self

  def keys_to_action(self, keys: environment.Keys):
    return self._send(Cmd.KEYS_TO_ACTION, keys)

  def user_input_to_action(self, user_input: environment.UserInput):
    return self._send(Cmd.USER_INPUT_TO_ACTION, user_input)

  def render(self) -> environment.Image:
    return self._send(Cmd.RENDER)

  def set_camera(self, index: int) -> Optional[environment.Camera]:
    return self._send(Cmd.SET_CAMERA, index)

  def metadata(self) -> environment.Metadata:
    return self._send(Cmd.METADATA)

  # dm_env.Environment methods.

  def reset(self) -> dm_env.TimeStep:
    return self._send(Cmd.RESET)

  def step(self, action) -> dm_env.TimeStep:
    return self._send(Cmd.STEP, action)

  def observation_spec(self):
    return self._send(Cmd.OBSERVATION_SPEC)

  def action_spec(self):
    return self._send(Cmd.ACTION_SPEC)

  def close(self):
    # TODO(sertan): We may want to free resources is the underlying environment
    # doesn't do so upon close() call.
    self._send(Cmd.CLOSE)


def _execute_cmd(env: environment.Environment, cmd: Cmd, args):
  """Executes the specified environment command and returns the result."""
  denv = env.env()
  if cmd == Cmd.KEYS_TO_ACTION:
    return env.keys_to_action(args)
  elif cmd == Cmd.USER_INPUT_TO_ACTION:
    return env.user_input_to_action(args)
  elif cmd == Cmd.RENDER:
    return env.render()
  elif cmd == Cmd.SET_CAMERA:
    return env.set_camera(args)
  elif cmd == Cmd.METADATA:
    return env.metadata()
  elif cmd == Cmd.RESET:
    return denv.reset()
  elif cmd == Cmd.STEP:
    return denv.step(args)
  elif cmd == Cmd.OBSERVATION_SPEC:
    return denv.observation_spec()
  elif cmd == Cmd.ACTION_SPEC:
    return denv.action_spec()
  elif cmd == Cmd.CLOSE:
    return denv.close()
  raise ValueError(f'Unknown command {cmd}.')


# Callback to create an environment from its specification.
CreateEnvFn = Callable[[study_pb2.EnvironmentSpec], environment.Environment]


def _proxy_handler(conn: multiprocessing.connection.Connection,
                   env_spec: study_pb2.EnvironmentSpec,
                   create_env_fn: CreateEnvFn):
  """Proxy handler in the child process."""
  env = None
  try:
    while True:
      cmd, args = conn.recv()
      logging.debug('Received command %s.', cmd)
      if cmd == Cmd.QUIT:
        break
      try:
        if cmd == Cmd.INIT:
          env = create_env_fn(env_spec)
          resp = True
        elif not env:
          resp = ValueError('Environment is not initialized.')
        else:
          resp = _execute_cmd(env, cmd, args)
      except Exception as e:
        # Exceptions due to command executions.
        resp = e
      conn.send(resp)
    conn.send(True)  # Acknowledges QUIT.
  except Exception:
    # Exceptions due to send or recv calls.
    logging.exception('Proxy handler exception')
  finally:
    conn.close()


def create_proxied_env_from_spec(
    env_spec: study_pb2.EnvironmentSpec,
    create_env_fn: CreateEnvFn) -> environment.Environment:
  """Returns a proxied environment that runs in a separate process."""
  parent_conn, child_conn = multiprocessing.Pipe()
  p = multiprocessing.Process(
      target=_proxy_handler, args=(child_conn, env_spec, create_env_fn))
  p.start()
  return EnvironmentProxy(parent_conn, p)
