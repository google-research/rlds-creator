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

"""SQLAlchemy storage for RLDS Creator."""

import datetime
from typing import Callable, List, Optional
import uuid

from absl import logging
from rlds_creator import storage
from rlds_creator import study_pb2
import sqlalchemy as sa


def _build_study_spec(study_spec: study_pb2.StudySpec, state: int,
                      creation_time: datetime.datetime) -> study_pb2.StudySpec:
  """Sets the fields of the study spec and returns it."""
  study_spec.state = state
  study_spec.creation_time.FromDatetime(creation_time)
  return study_spec


class ProtobufType(sa.TypeDecorator):
  """SQL type for a serialized protocol buffer message."""

  impl = sa.LargeBinary

  def __init__(self, cls):
    """Creates a ProtobufType for a protocol buffer message class.

    Args:
      cls: a protocol buffer message class.
    """
    super().__init__()
    self._cls = cls

  def process_bind_param(self, value, dialect) -> str:
    """Returns the serialized form of the protocol buffer message."""
    assert isinstance(value, self._cls)
    return value.SerializeToString()

  def process_result_value(self, value: str, dialect):
    """Parses the serialized protocol buffer message."""
    pb = self._cls()
    pb.ParseFromString(value)
    return pb


class Storage(storage.Storage):
  """SQLAlchemy based storage for RLDS Creator."""

  def __init__(self, engine: sa.engine.Engine, create_tables: bool = False):
    # Enable foreign key constraints.
    engine.execute('PRAGMA foreign_keys = ON')

    metadata = sa.MetaData()
    # Table that contains the studies.
    self._studies = sa.Table(
        'Studies',
        metadata,
        sa.Column('StudyId', sa.String, primary_key=True),
        sa.Column('State', sa.Integer),
        sa.Column('Spec', ProtobufType(study_pb2.StudySpec)),
        sa.Column('Timestamp', sa.DateTime),
        # Additional fields that can be queried.
        sa.Column('CreatorEmail', sa.String),
    )

    # Table that contains the study sessions.
    self._sessions = sa.Table(
        'StudySessions',
        metadata,
        sa.Column(
            'StudyId',
            sa.String,
            sa.ForeignKey('Studies.StudyId'),
            primary_key=True),
        sa.Column('SessionId', sa.String, primary_key=True),
        sa.Column('Session', ProtobufType(study_pb2.Session)),
        sa.Column('Timestamp', sa.DateTime),
    )

    # Table that contains the session episodes.
    self._episodes = sa.Table(
        'StudySessionEpisodes',
        metadata,
        sa.Column('StudyId', sa.String, primary_key=True),
        sa.Column('SessionId', sa.String, primary_key=True),
        sa.Column('EpisodeId', sa.String, primary_key=True),
        sa.Column('Episode', ProtobufType(study_pb2.Episode)),
        sa.Column('Timestamp', sa.DateTime),
        # Additional fields that can be queried.
        sa.Column('UserEmail', sa.String),
        sa.ForeignKeyConstraint(
            ['StudyId', 'SessionId'],
            ['StudySessions.StudyId', 'StudySessions.SessionId']),
    )

    if create_tables:
      metadata.create_all(engine)

    self._engine = engine

  def _execute(self, stmt) -> sa.engine.ResultProxy:
    """Executes the specified SQL statement."""
    return self._engine.execute(stmt)

  def create_study(self, study_spec: study_pb2.StudySpec) -> str:
    """See storage.Storage."""
    study_id = uuid.uuid1().hex
    logging.info('Creating study with ID %s', study_id)
    study_spec.id = study_id
    now = datetime.datetime.now()
    study_spec.creation_time.FromDatetime(now)
    s = self._studies.insert().values(
        StudyId=study_id,
        State=study_spec.state,
        Spec=study_spec,
        Timestamp=now,
        CreatorEmail=study_spec.creator.email)
    self._execute(s)
    return study_id

  def get_study(self, study_id: str) -> Optional[study_pb2.StudySpec]:
    """See storage.Storage."""
    s = sa.sql.select([self._studies
                      ]).where(self._studies.c.StudyId == study_id)
    row = self._execute(s).fetchone()
    if not row:
      return None
    return _build_study_spec(row['Spec'], row['State'], row['Timestamp'])

  def update_study_state(self, study_id: str, state: study_pb2.StudySpec.State):
    """See storage.Storage."""
    s = self._studies.update().where(
        self._studies.c.StudyId == study_id).values(State=state)
    # Row count denote the number of matched rows.
    if not self._execute(s).rowcount:
      raise ValueError('Missing study.')

  def update_study(self, study_spec: study_pb2.StudySpec):
    """See storage.Storage."""
    s = self._studies.update().where(
        self._studies.c.StudyId == study_spec.id).values(Spec=study_spec)
    # Row count denote the number of matched rows.
    if not self._execute(s).rowcount:
      raise ValueError('Missing study.')

  def get_studies(self,
                  state: Optional[int] = None,
                  email: Optional[str] = None) -> List[study_pb2.StudySpec]:
    """See storage.Storage."""
    s = sa.sql.select([self._studies])
    if state is not None:
      s = s.where(self._studies.c.State == state)
    if email is not None:
      s = s.where(self._studies.c.CreatorEmail == email)
    s = s.order_by(self._studies.c.Timestamp)
    rows = self._execute(s)
    return [
        _build_study_spec(row['Spec'], row['State'], row['Timestamp'])
        for row in rows
    ]

  def create_session(self, session: study_pb2.Session) -> None:
    """See storage.Storage."""
    storage.validate_session(session)
    logging.info('Creating session with ID %s for study %s.', session.id,
                 session.study_id)
    s = self._sessions.insert().values(
        StudyId=session.study_id,
        SessionId=session.id,
        Session=session,
        Timestamp=session.start_time.ToDatetime())
    try:
      self._execute(s)
    except sa.exc.IntegrityError:
      raise ValueError('Missing study.')

  def update_session(self, session: study_pb2.Session) -> None:
    """See storage.Storage."""
    storage.validate_session(session)
    s = self._sessions.update().where(
        (self._sessions.c.StudyId == session.study_id)
        & (self._sessions.c.SessionId == session.id)).values(Session=session)
    if not self._execute(s).rowcount:
      raise ValueError('Missing session.')

  def get_session(self, study_id: str,
                  session_id: str) -> Optional[study_pb2.Session]:
    """See storage.Storage."""
    s = sa.sql.select([self._sessions
                      ]).where((self._sessions.c.StudyId == study_id)
                               & (self._sessions.c.SessionId == session_id))
    row = self._execute(s).fetchone()
    return row['Session'] if row else None

  def create_episode(self, episode: study_pb2.Episode) -> None:
    """See storage.Storage."""
    storage.validate_episode(episode)
    logging.info('Saving episode with ID %s for session %s in study %s.',
                 episode.id, episode.session_id, episode.study_id)
    s = self._episodes.insert().values(
        StudyId=episode.study_id,
        SessionId=episode.session_id,
        EpisodeId=episode.id,
        Episode=episode,
        Timestamp=episode.start_time.ToDatetime(),
        UserEmail=episode.user.email)
    try:
      self._execute(s)
    except sa.exc.IntegrityError:
      raise ValueError('Missing study or session.')

  def _episode_matches(self, study_id: str, session_id: str, episode_id: str):
    """Returns an SQL condition that matches the specified episode."""
    return ((self._episodes.c.StudyId == study_id)
            & (self._episodes.c.SessionId == session_id)
            & (self._episodes.c.EpisodeId == episode_id))

  def get_episode(self, study_id: str, session_id: str,
                  episode_id: str) -> Optional[study_pb2.Episode]:
    s = sa.sql.select([self._episodes]).where(
        self._episode_matches(study_id, session_id, episode_id))
    row = self._execute(s).fetchone()
    return row['Episode'] if row else None

  def atomic_update_episode(
      self, study_id: str, session_id: str, episode_id: str,
      callback: Callable[[study_pb2.Episode], bool]) -> bool:
    """See storage.Storage."""
    cond = self._episode_matches(study_id, session_id, episode_id)
    # Start a transaction.
    with self._engine.begin() as conn:
      s = sa.sql.select([self._episodes]).where(cond)
      row = conn.execute(s).fetchone()
      if not row:
        # Episode is missing.
        return False
      episode = row['Episode']
      if not callback(episode):
        # Callback rejects the update.
        return False
      if (episode.study_id != study_id or episode.session_id != session_id or
          episode.id != episode_id):
        # ID change is not allowed.
        return False
      s = self._episodes.update().where(cond).values(Episode=episode)
      if conn.execute(s).rowcount != 1:
        # Normally this should not happen, but we handle it gracefully.
        raise ValueError('Missing episode.')
      return True

  def get_episodes(self,
                   study_id: str,
                   email: Optional[str] = None) -> List[study_pb2.Episode]:
    """See storage.Storage."""
    s = sa.sql.select([self._episodes
                      ]).where(self._episodes.c.StudyId == study_id)
    if email is not None:
      s = s.where(self._episodes.c.UserEmail == email)
    s = s.order_by(self._episodes.c.Timestamp.desc())
    rows = self._execute(s)
    return [row['Episode'] for row in rows]

  def delete_episode(self, study_id: str, session_id: str,
                     episode_id: str) -> bool:
    """See storage.Storage."""
    s = self._episodes.delete().where(
        self._episode_matches(study_id, session_id, episode_id))
    return self._execute(s).rowcount == 1
