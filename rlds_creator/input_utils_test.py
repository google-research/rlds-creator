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

"""Tests for rlds_creator.input_utils."""

from absl.testing import absltest
from rlds_creator import input_utils


class InputUtilsTest(absltest.TestCase):

  def test_get_key_mapping(self):
    self.assertDictEqual(
        input_utils.get_key_mapping({
            'a': ['x', 'y'],
            1: ['u', 'v']
        }), {
            'x': 'a',
            'y': 'a',
            'u': 1,
            'v': 1
        })

  def test_get_mapped_keys(self):
    self.assertDictEqual(
        input_utils.get_mapped_keys({
            'a': 0.5,
            'b': 1,
            'c': -0.5,
            'd': -1.0
        }, {
            'b': 'x',
            'd': 'c'
        }),
        {
            'a': 0.5,
            'x': 1,
            # d gets mapped to c and it should overwrite the existing value.
            'c': -1.0
        })

  def test_axes_to_keys(self):
    keys = {'axis1': 0.6, 'axis2': 0.4, 'axis3': -0.6, 'axis4': -0.4, 'x': 1}
    mapping = {
        'axis1': ('low1', 'high1'),
        'axis2': ('low2', 'high2'),
        'axis3': ('low3', 'high3'),
        'axis4': ('low4', 'high4')
    }
    self.assertDictEqual(
        input_utils.axes_to_keys(keys, threshold=0.5, mapping=mapping), {
            'high1': 1,
            'low3': 1
        })
    self.assertDictEqual(
        input_utils.axes_to_keys(keys, threshold=0.4, mapping=mapping), {
            'high1': 1,
            'high2': 1,
            'low3': 1,
            'low4': 1
        })
    self.assertDictEqual(
        input_utils.axes_to_keys(keys, threshold=0.61, mapping=mapping), {})


if __name__ == '__main__':
  absltest.main()
