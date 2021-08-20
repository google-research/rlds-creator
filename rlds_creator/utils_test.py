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

"""Tests for utils."""

from absl.testing import absltest
from rlds_creator import utils


class UtilsTest(absltest.TestCase):

  def test_get_agent_id(self):
    self.assertEqual(
        '8ed1a0d61d92bf1cc932786eac3b9680d2426a947aa94b8f850283c7b9976947',
        utils.get_agent_id('study', 'user@test.com'))
    self.assertEqual(
        '6cd972ffc98e00acfc137c6ae8f315ef896513c9b923a8652756aef3bc8e2852',
        utils.get_agent_id('other_study', 'user@test.com'))
    self.assertEqual(
        'b85c3ada0b02f31dc0f6743189ac9230822fbb4a57bb2dffec51fe104ac824d4',
        utils.get_agent_id('study', 'other@test.com'))

  def test_get_metadata_key(self):
    self.assertEqual('rlds_creator:foo', utils.get_metadata_key('foo'))

  def test_get_public_episode_id(self):
    self.assertEqual(
        '6b5afca408fe2868b46c0c80acefabf5de093eeff9d39e27f16d345fa43b1607',
        utils.get_public_episode_id('study', 'episode'))
    self.assertEqual(
        'd75d27d5f703c447e3b6e0031db26591664b1943d41674b42c303f158da26d20',
        utils.get_public_episode_id('study', 'other_episode'))
    self.assertEqual(
        '457b1c54431b799247c9057fbb0e3a10563a2d8bf8d38e9150e3b50015bc8876',
        utils.get_public_episode_id('other_study', 'episode'))


if __name__ == '__main__':
  absltest.main()
