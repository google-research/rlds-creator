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

"""Tests for rlds_creator.sqlalchemy_storage."""

from absl.testing import absltest
from rlds_creator import sqlalchemy_storage
from rlds_creator import storage_test_util
import sqlalchemy
import sqlite3


class SqlalchemyStorageTest(storage_test_util.StorageTest):

  def setUp(self):
    super().setUp()
    engine = sqlalchemy.create_engine('sqlite:///:memory:', echo=True)
    self._storage = sqlalchemy_storage.Storage(engine, create_tables=True)

  @property
  def storage(self) -> sqlalchemy_storage.Storage:
    return self._storage

  def test_delete_episode(self):
    episode = self._create_sample_episode()
    self.assertTrue(
        self.storage.delete_episode(episode.study_id, episode.session_id,
                                    episode.id))
    # Deleting again should return false.
    self.assertFalse(
        self.storage.delete_episode(episode.study_id, episode.session_id,
                                    episode.id))

  def test_delete_missing_episode(self):
    self.assertFalse(self.storage.delete_episode('study', 'session', 'episode'))


if __name__ == '__main__':
  absltest.main()
