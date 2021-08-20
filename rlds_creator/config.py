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

"""RLDS Creator configuration."""

import re

from procgen import env as procgen_env
import robosuite
from robosuite import controllers as robosuite_controllers



# IDs of Procgen environments and their labels.
PROCGEN_IDS = [{
    'id': env,
    'label': env.capitalize()
} for env in procgen_env.ENV_NAMES]

# See list_games() in third_party/py/atari_py/games.py.
ATARI_GAMES = [
    'Alien', 'Amidar', 'Assault', 'Asterix', 'Asteroids', 'Atlantis',
    'BankHeist', 'BattleZone', 'BeamRider', 'Berzerk', 'Bowling', 'Boxing',
    'Breakout', 'Centipede', 'ChopperCommand', 'CrazyClimber', 'Defender',
    'DemonAttack', 'DoubleDunk', 'Enduro', 'FishingDerby', 'Freeway',
    'Frostbite', 'Gopher', 'Gravitar', 'Hero', 'IceHockey', 'Jamesbond',
    'Kangaroo', 'Krull', 'KungFuMaster', 'MontezumaRevenge', 'MsPacman',
    'NameThisGame', 'Phoenix', 'Pitfall', 'Pong', 'PrivateEye', 'Qbert',
    'Riverraid', 'RoadRunner', 'Robotank', 'Seaquest', 'Skiing', 'Solaris',
    'SpaceInvaders', 'StarGunner', 'Surround', 'Tennis', 'TimePilot',
    'Tutankham', 'UpNDown', 'Venture', 'VideoPinball', 'WizardOfWor',
    'YarsRevenge', 'Zaxxon'
]

# IDs of Atari environment and their labels.
ATARI_IDS = [{'id': game, 'label': game} for game in ATARI_GAMES]

# See game_scripts/levels/contributed/dmlab30 under deepmind_lab.
DMLAB_LEVELS = [
    'rooms_collect_good_objects_train',
    'rooms_collect_good_objects_test',
    'rooms_exploit_deferred_effects_train',
    'rooms_exploit_deferred_effects_test',
    'rooms_select_nonmatching_object',
    'rooms_watermaze',
    'rooms_keys_doors_puzzle',
    'language_select_described_object',
    'language_select_located_object',
    'language_execute_random_task',
    'language_answer_quantitative_question',
    'lasertag_one_opponent_small',
    'lasertag_three_opponents_small',
    'lasertag_one_opponent_large',
    'lasertag_three_opponents_large',
    'natlab_fixed_large_map',
    'natlab_varying_map_regrowth',
    'natlab_varying_map_randomized',
    'skymaze_irreversible_path_hard',
    'skymaze_irreversible_path_varied',
    'psychlab_arbitrary_visuomotor_mapping',
    'psychlab_continuous_recognition',
    'psychlab_sequential_comparison',
    'psychlab_visual_search',
    'explore_object_locations_small',
    'explore_object_locations_large',
    'explore_obstructed_goals_small',
    'explore_obstructed_goals_large',
    'explore_goal_locations_small',
    'explore_goal_locations_large',
    'explore_object_rewards_few',
    'explore_object_rewards_many',
]


def dmlab_level_label(level) -> str:
  """Returns the label for a DMLab level."""
  return level.replace('_', ' ').title()


# IDs of DMLab environments and their labels.
DMLAB_IDS = [{
    'id': level,
    'label': dmlab_level_label(level)
} for level in DMLAB_LEVELS]

NET_HACK_IDS = [
    {
        'id': 'NetHack-v0',
        'label': 'Default'
    },
    {
        'id': 'NetHackScore-v0',
        'label': 'Score'
    },
    {
        'id': 'NetHackStaircase-v0',
        'label': 'Staircase'
    },
    {
        'id': 'NetHackStaircasePet-v0',
        'label': 'Staircase Pet'
    },
    {
        'id': 'NetHackOracle-v0',
        'label': 'Oracle'
    },
    {
        'id': 'NetHackGold-v0',
        'label': 'Gold'
    },
    {
        'id': 'NetHackEat-v0',
        'label': 'Eat'
    },
    {
        'id': 'NetHackScout-v0',
        'label': 'Scout'
    },
    {
        'id': 'NetHackChallenge-v0',
        'label': 'Challenge'
    },
]

ROBODESK_TASKS = [
    {
        'id': 'open_slide',
        'label': 'Open slide'
    },
    {
        'id': 'open_drawer',
        'label': 'Open drawer'
    },
    {
        'id': 'push_green',
        'label': 'Push green'
    },
    {
        'id': 'stack',
        'label': 'Stack'
    },
    {
        'id': 'upright_block_off_table',
        'label': 'Upright block off table'
    },
    {
        'id': 'flat_block_in_bin',
        'label': 'Flat block in bin'
    },
    {
        'id': 'flat_block_in_shelf',
        'label': 'Flat block in shelf'
    },
    {
        'id': 'lift_upright_block',
        'label': 'Lift upright block'
    },
    {
        'id': 'lift_ball',
        'label': 'Lift ball'
    },
]

ROBOSUITE_IDS = [{
    'id': env,
    'label': re.sub(r'([A-Z])', r' \1', env)
} for env in robosuite.ALL_ENVIRONMENTS]

ROBOSUITE_ROBOTS = [{
    'id': robot,
    'label': robot
} for robot in robosuite.ALL_ROBOTS]

ROBOSUITE_CONFIGS = [{
    'id': 'single-arm-opposed',
    'label': 'Single Arms Opposed'
}, {
    'id': 'single-arm-parallel',
    'label': 'Single Arms Parallel'
}, {
    'id': 'bimanual',
    'label': 'Bimanual'
}]

ROBOSUITE_ARMS = [{
    'id': 'right',
    'label': 'Right'
}, {
    'id': 'left',
    'label': 'Left'
}]

ROBOSUITE_CONTROLLERS = [{
    'id': controller,
    'label': name
} for controller, name in robosuite_controllers.CONTROLLER_INFO.items()]

ROBOSUITE_CAMERAS = [{
    'id': 'agentview',
    'label': 'Agent view'
}, {
    'id': 'frontview',
    'label': 'Front view'
}, {
    'id': 'birdview',
    'label': 'Bird view'
}, {
    'id': 'sideview',
    'label': 'Side view'
}, {
    'id': 'robot0_robotview',
    'label': 'Robot view'
}, {
    'id': 'robot0_eye_in_hand',
    'label': 'Robot eye in hand view',
}]



CONFIG = {
    'atari': {
        'ids': ATARI_IDS
    },
    'dmlab': {
        'ids': DMLAB_IDS
    },
    'net_hack': {
        'ids': NET_HACK_IDS
    },
    'procgen': {
        'ids': PROCGEN_IDS
    },
    'robodesk': {
        'tasks': ROBODESK_TASKS
    },
    'robosuite': {
        'ids': ROBOSUITE_IDS,
        'robots': ROBOSUITE_ROBOTS,
        'configs': ROBOSUITE_CONFIGS,
        'arms': ROBOSUITE_ARMS,
        'controllers': ROBOSUITE_CONTROLLERS,
        'cameras': ROBOSUITE_CAMERAS,
    },
}
