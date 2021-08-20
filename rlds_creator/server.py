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

"""Basic RLDS Creator server."""

import asyncio
import os
from typing import Awaitable, Optional, Sequence

from absl import app
from absl import flags
from rlds_creator import client_pb2
from rlds_creator import config
from rlds_creator import environment
from rlds_creator import environment_factory
from rlds_creator import environment_handler
from rlds_creator import episode_storage
from rlds_creator import episode_storage_factory
from rlds_creator import pickle_episode_storage
from rlds_creator import sqlalchemy_storage
from rlds_creator import study_pb2
import sqlalchemy
import sqlite3
from tornado import web
import tornado.ioloop
import tornado.websocket

import deepmind_lab

FLAGS = flags.FLAGS

flags.DEFINE_integer(
    'port', 8888, 'port to listen for HTTP requests', lower_bound=1)
flags.DEFINE_string(
    'base_log_dir', '/tmp/rlds_creator_logs',
    'Directory for storing the episode logs. Episodes from a session will be '
    'under its own subdirectory. If None, logging will be disabled.')
flags.DEFINE_string('db_path', 'sqlite:///:memory:', 'Path of the database.')
flags.DEFINE_string('static_files_path', 'static',
                    'Relative path of the static files.')
flags.DEFINE_boolean('record_videos', False, 'Enables video recording.')

# Path to the static resources.
_RESOURCES_PATH = os.path.dirname(__file__)
# Default timeout in seconds for the socket operations.
_DEFAULT_TIMEOUT_SECS = 60


class EnvironmentHandler(environment_handler.EnvironmentHandler):
  """Environment handler that creates the environments using the factory."""

  def __init__(self, web_socket, *args, **kwargs):
    self._web_socket = web_socket
    self._ioloop = tornado.ioloop.IOLoop.current()
    super().__init__(*args, **kwargs)

  def create_env_from_spec(
      self, env_spec: study_pb2.EnvironmentSpec) -> environment.Environment:
    return environment_factory.create_env_from_spec(env_spec)

  def get_url_for_path(self, path: str) -> str:
    return 'file://' + path

  def create_episode_writer(
      self,
      env: environment.DMEnv,
      path: str,
      metadata: Optional[episode_storage.EnvironmentMetadata] = None
  ) -> episode_storage.EpisodeWriter:
    return pickle_episode_storage.PickleEpisodeWriter(env, path, metadata)

  def _write_message(self,
                     response: client_pb2.OperationResponse) -> Awaitable[None]:
    """Writes the response to the websocket and returns the future."""
    return self._web_socket.write_message(
        response.SerializeToString(), binary=True)

  def send_response(self, response: client_pb2.OperationResponse) -> bool:
    # Send the message and wait. Unlike the regular Futures API, the result()
    # method of the future returned by write_message() call cannot be called
    # directly (the future may not be in done state which raises an exception).
    try:
      # send_response() method may be called from a different thread than the
      # main thread of the environment handler (e.g. steps of asynchronous
      # environments). We use call_soon_threadsafe() to ensure that the IO
      # operation is executed by the event loop of the handler.
      asyncio.wait_for(
          self._ioloop.asyncio_loop.call_soon_threadsafe(
              self._write_message, response),
          timeout=_DEFAULT_TIMEOUT_SECS)
    except asyncio.TimeoutError:
      return False
    return True

  def on_close(self):
    pass


class EnvironmentWebSocketHandler(tornado.websocket.WebSocketHandler):
  """Handler for the environment web socket."""

  def __init__(self, *args, **kwargs):
    self._handler = None
    super().__init__(*args, **kwargs)

  def open(self):
    self._handler = EnvironmentHandler(
        self,
        self.application.settings.get('storage'),
        study_pb2.User(email='user@localhost'),
        config.CONFIG,
        episode_storage_factory.EpisodeStorageFactory(),
        base_log_dir=FLAGS.base_log_dir,
        record_videos=FLAGS.record_videos)

  def on_message(self, message):
    request = client_pb2.OperationRequest()
    request.ParseFromString(message)
    self._handler.handle_request(request)

  def on_close(self):
    # The initialization of the environment handler might have failed.
    if self._handler:
      self._handler.close()


def main(argv: Sequence[str]) -> None:
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')


  # Create the storage.
  engine = sqlalchemy.create_engine(FLAGS.db_path)
  storage = sqlalchemy_storage.Storage(engine=engine, create_tables=True)

  web_app = web.Application([
      (r'/static/(.*)', web.StaticFileHandler, {
          'path': os.path.join(_RESOURCES_PATH, FLAGS.static_files_path)
      }),
      (r'/', web.RedirectHandler, {
          'url': '/static/app.html'
      }),
      (r'/channel/environment', EnvironmentWebSocketHandler),
  ],
                            storage=storage)

  web_app.listen(FLAGS.port)
  tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
  app.run(main)
