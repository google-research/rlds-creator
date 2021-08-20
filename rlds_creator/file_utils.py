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

"""File utilities."""

import distutils.dir_util
import distutils.file_util
import os
from typing import AnyStr, List, Generator, IO, Tuple


def copy(src: str, dst: str, overwrite: bool = False):
  """Copies the source file to destination."""
  if not overwrite and os.path.exists(dst):
    return
  distutils.file_util.copy_file(src, dst)


def recursively_copy_dir(src: str, dst: str):
  """Recursively copies the files from source to destination directory."""
  distutils.dir_util.copy_tree(src, dst)


def make_dirs(path: str):
  """Creates a directory and all parent/intermediate directories."""
  distutils.dir_util.mkpath(path)


def open_file(path: str, mode: str) -> IO[AnyStr]:
  """Opens a file."""
  return open(path, mode)


def mtime(path: str) -> int:
  """Returns the modification time of the specified file or directory."""
  return int(os.stat(path).st_mtime)


def delete_recursively(path: str):
  """Deletes everything under path recursively."""
  if os.path.isdir(path):
    distutils.dir_util.remove_tree(path)
  else:
    os.remove(path)


def walk(top: str) -> Generator[Tuple[str, List[str], List[str]], None, None]:
  """Recursive directory tree generator for directories.

  Args:
    top: a directory name.

  Yields:
    a tuple that contains the pathname of a directory, followed by lists of all
    its subdirectories and leaf files
  """
  yield from os.walk(top)
