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

"""Tests for the Riegeli episode storage."""

import os

from absl.testing import absltest
from rlds_creator import constants
from rlds_creator import riegeli_episode_storage
from rlds_creator import test_utils

ENV_ID = 'maze'


class RiegeliEpisodeStorageTest(absltest.TestCase):

  def test_write_and_read(self):
    env = test_utils.create_env(ENV_ID, max_episode_steps=10)
    denv = env.env()
    basedir = self.create_tempdir()
    env_metadata = {'foo': 1, 'bar': 2}
    writer = riegeli_episode_storage.RiegeliEpisodeWriter(
        denv, basedir.full_path, env_metadata)
    # Record two episodes.
    episodes = []
    for index in range(2):
      episode_metadata = {'custom': index}
      episode, _, _ = test_utils.record_episode(
          writer,
          f'episode{index}',
          ENV_ID,
          env,
          episode_metadata=episode_metadata)
      episodes.append(episode)

    writer.close()

    for index, episode in enumerate(episodes):
      path = episode.storage.environment_logger.tag_directory
      # Check that the directory containing the Riegeli files exists.
      self.assertTrue(os.path.exists(path))

      reader = riegeli_episode_storage.RiegeliEpisodeReader(path, index)
      self.assertDictEqual(
          {
              'agent_id': test_utils.AGENT_ID,
              'custom': index,
              'episode_id': f'episode{index}',
              'rlds_creator:env_id': ENV_ID,
              'rlds_creator:study_id': test_utils.STUDY_ID,
          }, reader.metadata)

      self.assertEqual(denv.action_spec(), reader.action_spec())
      self.assertEqual(denv.discount_spec(), reader.discount_spec())
      self.assertEqual(denv.observation_spec(), reader.observation_spec())
      self.assertEqual(denv.reward_spec(), reader.reward_spec())

      # Including the initial state.
      self.assertLen(reader.steps, episode.num_steps + 1)

      # Custom data should be present in the steps.
      for step in reader.steps:
        self.assertIn(constants.METADATA_IMAGE, step.custom_data)


if __name__ == '__main__':
  absltest.main()
