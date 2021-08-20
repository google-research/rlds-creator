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

"""Tests for net_hack_env."""

from absl.testing import absltest
from rlds_creator import study_pb2
from rlds_creator.envs import net_hack_env


class NetHackEnvTest(absltest.TestCase):

  def test_create(self):
    env = net_hack_env.NetHackEnvironment(
        study_pb2.EnvironmentSpec(
            max_episode_steps=100,
            net_hack=study_pb2.EnvironmentSpec.NetHack(id='NetHackScore-v0')))

    dm_env = env.env()
    # NetHack observation is a dictionary.
    self.assertSetEqual(
        set(dm_env.observation_spec().keys()), {
            'blstats',
            'chars',
            'colors',
            'glyphs',
            'inv_glyphs',
            'inv_letters',
            'inv_oclasses',
            'inv_strs',
            'message',
            'screen_descriptions',
            'specials',
            'tty_chars',
            'tty_colors',
            'tty_cursor',
        })
    self.assertEqual(dm_env.action_spec().shape, ())

    dm_env.reset()
    image = env.render()
    self.assertEqual(image.shape, (263, 484, 3))

    # Sanity check. Movement keys.
    keys = {'l': 2, 'k': 1, 'j': 3, 'h': 4}
    for key, action in keys.items():
      self.assertEqual(env.keys_to_action({key: 1}), action)


if __name__ == '__main__':
  absltest.main()
