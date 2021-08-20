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

"""Tests for the renderer."""

import io

from absl.testing import absltest
import numpy as np
from PIL import Image
from PIL import ImageChops
from rlds_creator import renderer


class RendererTest(absltest.TestCase):

  def test_encode_image(self):
    # A random image.
    image = np.random.randint(0, 256, (16, 16, 3), dtype=np.uint8)
    encoded = renderer.Renderer.encode_image(image, fmt='PNG')
    # Check that the decoded image is the same.
    decoded = Image.open(io.BytesIO(encoded))
    self.assertEqual((16, 16), decoded.size)
    diff = ImageChops.difference(Image.fromarray(image), decoded)
    self.assertFalse(diff.getbbox())


if __name__ == '__main__':
  absltest.main()
