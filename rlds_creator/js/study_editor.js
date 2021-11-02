// Copyright 2021 RLDSCreator Authors.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @fileoverview Study editor.
 */
goog.module('rlds_creator.studyEditor');

const EnvironmentSpec = goog.require('proto.rlds_creator.EnvironmentSpec');
const EventTarget = goog.require('goog.events.EventTarget');
const Select = goog.require('goog.ui.Select');
const StudySpec = goog.require('proto.rlds_creator.StudySpec');
const dom = goog.require('goog.dom');
const events = goog.require('goog.events');
const {
    checkCheckbox,
    checkRadio,
    createCheckbox,
    createSelect,
    getElement,
    isChecked,
    setTextField,
    showElement
} = goog.require('rlds_creator.utils');

const ProcgenDistributionMode = EnvironmentSpec.Procgen.DistributionMode;
const RoboDeskReward = EnvironmentSpec.RoboDesk.Reward;

/**
 * Study editor.
 */
class StudyEditor extends EventTarget {
    /**
     * Returns the string representation of the environment type used in the
     * element IDs.
     *
     * @param {!EnvironmentSpec.TypeCase} envType Type of the environment.
     * @return {string}
     * @private
     */
    static getEnvTypeId_(envType) {
        switch (envType) {
            case EnvironmentSpec.TypeCase.ATARI:
                return 'atari';
            case EnvironmentSpec.TypeCase.DMLAB:
                return 'dmlab';
            case EnvironmentSpec.TypeCase.NET_HACK:
                return 'net-hack';
            case EnvironmentSpec.TypeCase.PROCGEN:
                return 'procgen';
            case EnvironmentSpec.TypeCase.ROBODESK:
                return 'robodesk';
            case EnvironmentSpec.TypeCase.ROBOSUITE:
                return 'robosuite';
            default:
                return '';
        }
    }

    /**
     * Returns the ID prefixed by the ID of the editor which is the prefix for its
     * elements.
     *
     * @param {string} id Unprefixed ID.
     * @return {string}
     * @private
     */
    getId_(id) {
        return this.id_ + id;
    }


    /**
     * Returns the element with the specified unprefixed ID.
     *
     * @param {string} id Unprefixed ID.
     * @return {?Element}
     * @private
     */
    getElement_(id) {
        return getElement(this.getId_(id));
    }

    /**
     * Returns the value of a text field with the specified unprefixed ID.
     *
     * @param {string} id
     * @return {string}
     * @private
     */
    getText_(id) {
        return /** @type {!HTMLInputElement} */ (this.getElement_(id)).value;
    }

    /**
     * Sets the value of a text field with the specified unprefixed ID.
     *
     * @param {string} id
     * @param {string} value
     * @private
     */
    setText_(id, value) {
        setTextField(this.getId_(id), value);
    }

    /**
     * Calls the function with a number based on the value of the text field with
     * the specified unprefixed ID if the value is not empty.
     *
     * @param {string} id Unprefixed ID of the text field.
     * @param {function(number)}  fn Function to set the numeric value.
     * @private
     */
    maybeSetNumber_(id, fn) {
        const value = this.getText_(id);
        if (value !== '') {
            fn(parseInt(value, 10));
        }
    }

    /**
     * Calls the function with a floating number based on the value of the text
     * field with the specified unprefixed ID if the value is not empty.
     *
     * @param {string} id Unprefixed ID of the text field.
     * @param {function(number)}  fn Function to set the floating number value.
     * @private
     */
    maybeSetFloat_(id, fn) {
        const value = this.getText_(id);
        if (value !== '') {
            fn(parseFloat(value));
        }
    }

    /**
     * Returns true if the checkbox with the specified unprefixed ID is checked.
     *
     * @param {string} id
     * @return {boolean}
     * @private
     */
    isChecked_(id) {
        return isChecked(this.getId_(id));
    }

    /**
     * Shows the container that allows editing the environment with the specified
     * type.
     *
     * @param {!EnvironmentSpec.TypeCase} envType Type of the environment.
     * @param {boolean=} show Whether to show or hide the container.
     * @private
     */
    showEnvContainer_(envType, show = true) {
        if (envType != EnvironmentSpec.TypeCase.TYPE_NOT_SET) {
            showElement(
                this.getId_(StudyEditor.getEnvTypeId_(envType) + '-container'), show);
        }
    }

    constructor(id, config) {
        super();
        /** @const @private {string} */
        this.id_ = id;
        /** @private {?string} */
        this.studyId_ = null;
        /** @const @private {!HTMLElement} */
        this.panel_ =
            /** @type {!HTMLElement} */
            (this.getElement_('panel'));
        /** @private {!EnvironmentSpec.TypeCase} */
        this.lastEnvType_ = EnvironmentSpec.TypeCase.TYPE_NOT_SET;
        // Hide the environment containers.
        for (const id in EnvironmentSpec.TypeCase) {
            const envType = EnvironmentSpec.TypeCase[id];
            if (envType == EnvironmentSpec.TypeCase.TYPE_NOT_SET) {
                continue;
            }
            this.showEnvContainer_(envType, false);
            events.listen(
                this.getElement_(StudyEditor.getEnvTypeId_(envType)),
                events.EventType.CHANGE, e => this.selectEnv_(envType));
        }
        /** @const @private {!Select} */
        this.procgenId_ = createSelect(
            this.getId_('procgen-id'), this.getId_('procgen-ids'),
            'procgen' in config ? config['procgen']['ids'] : []);

        const procgenDistributionModes = [{
                'id': ProcgenDistributionMode.DISTRIBUTION_EASY,
                'label': 'Easy'
            },
            {
                'id': ProcgenDistributionMode.DISTRIBUTION_HARD,
                'label': 'Hard'
            },
            {
                'id': ProcgenDistributionMode.DISTRIBUTION_EXTREME,
                'label': 'Extreme'
            },
            {
                'id': ProcgenDistributionMode.DISTRIBUTION_MEMORY,
                'label': 'Memory'
            },
            {
                'id': ProcgenDistributionMode.DISTRIBUTION_EXPLORATION,
                'label': 'Exploration'
            },
        ];
        /** @const @private {!Select} */
        this.procgenDistributionMode_ = createSelect(
            this.getId_('procgen-distribution-mode'),
            this.getId_('procgen-distribution-modes'), procgenDistributionModes);
        /** @const @private {!Select} */
        this.atariId_ = createSelect(
            this.getId_('atari-id'), this.getId_('atari-ids'),
            'atari' in config ? config['atari']['ids'] : []);
        /** @const @private {!Select} */
        this.dmLabId_ = createSelect(
            this.getId_('dmlab-id'), this.getId_('dmlab-ids'),
            'dmlab' in config ? config['dmlab']['ids'] : []);
        /** @const @private {!Select} */
        this.netHackId_ = createSelect(
            this.getId_('net-hack-id'), this.getId_('net-hack-ids'),
            'net_hack' in config ? config['net_hack']['ids'] : []);
        const robodesk = config['robodesk'];
        /** @const @private {!Select} */
        this.robodeskTask_ = createSelect(
            this.getId_('robodesk-task'), this.getId_('robodesk-tasks'),
            robodesk ? robodesk['tasks'] : []);
        const robodeskRewards = [{
                'id': RoboDeskReward.REWARD_DENSE,
                'label': 'Dense'
            },
            {
                'id': RoboDeskReward.REWARD_SPARSE,
                'label': 'Sparse'
            },
            {
                'id': RoboDeskReward.REWARD_SUCCESS,
                'label': 'Success'
            },
        ];
        /** @const @private {!Select} */
        this.robodeskReward_ = createSelect(
            this.getId_('robodesk-reward'),
            this.getId_('robodesk-rewards'), robodeskRewards);
        const robosuite = config['robosuite'];
        /** @const @private {!Select} */
        this.robosuiteId_ = createSelect(
            this.getId_('robosuite-id'), this.getId_('robosuite-ids'),
            robosuite ? robosuite['ids'] : []);
        this.robosuiteRobot_ = createSelect(
            this.getId_('robosuite-robot'), this.getId_('robosuite-robots'),
            robosuite ? robosuite['robots'] : []);
        this.robosuiteConfig_ = createSelect(
            this.getId_('robosuite-config'), this.getId_('robosuite-configs'),
            robosuite ? robosuite['configs'] : []);
        this.robosuiteArm_ = createSelect(
            this.getId_('robosuite-arm'), this.getId_('robosuite-arms'),
            robosuite ? robosuite['arms'] : []);
        this.robosuiteController_ = createSelect(
            this.getId_('robosuite-controller'),
            this.getId_('robosuite-controllers'),
            robosuite ? robosuite['controllers'] : []);
        this.robosuiteCameras_ = [];
        if (robosuite) {
            const camerasContainer = this.getElement_('robosuite-cameras');
            for (const camera of robosuite['cameras']) {
                const cb = createCheckbox(
                    this.getId_('robosuite-camera-' + camera['id']), camera['label']);
                dom.appendChild(camerasContainer, cb);
                componentHandler.upgradeElement(cb);
                this.robosuiteCameras_.push(camera['id']);
            }
        }

        // Handle click events on cancel and save buttons.
        events.listen(this.getElement_('cancel'), events.EventType.CLICK, e => {
            if (this.dispatchEvent(events.EventType.RESET)) {
                this.reset();
            }
        });

        events.listen(this.getElement_('save'), events.EventType.CLICK, e => {
            if (this.dispatchEvent(events.EventType.SUBMIT)) {
                this.reset();
            }
        });
    }

    /**
     * Resets the editor.
     */
    reset() {
        this.studyId_ = null;
        this.selectEnv_(EnvironmentSpec.TypeCase.TYPE_NOT_SET);
        this.panel_.querySelectorAll('.mdl-textfield__input').forEach(function(el) {
            setTextField(el, '');
        });
        this.procgenId_.setValue(null);
        this.procgenDistributionMode_.setValue(null);
        this.atariId_.setValue(null);
        this.dmLabId_.setValue(null);
        this.netHackId_.setValue(null);
        this.robodeskTask_.setValue(null);
        this.robodeskReward_.setValue(null);
        this.robosuiteId_.setValue(null);
        this.robosuiteRobot_.setValue(null);
        this.robosuiteConfig_.setValue(null);
        this.robosuiteArm_.setValue(null);
        this.robosuiteController_.setValue(null);
        for (const camera of this.robosuiteCameras_) {
            checkCheckbox(this.getId_('robosuite-camera-' + camera), false);
        }
    }

    /**
     * Shows the options for the specified environment type and hides the previous
     * one, if any.
     *
     * @param {!EnvironmentSpec.TypeCase} envType Type of the environment.
     * @private
     */
    selectEnv_(envType) {
        // Hide the previous container and show the selected one.
        this.showEnvContainer_(this.lastEnvType_, false);
        this.showEnvContainer_(envType, true);
        this.lastEnvType_ = envType;
    }

    /**
     * Sets the study, i.e. populates the editor based on its specification.
     *
     * @param {!StudySpec} study Study specification.
     * @return {boolean} True on success or false.
     */
    setStudy(study) {
        this.studyId_ = study.getId();
        const envs = study.getEnvironmentSpecsList();
        if (envs.length > 1) {
            throw new Error('You cannot edit studies with multiple environments.');
        }
        this.setText_('name', study.getName());
        this.setText_('description', study.getDescription());
        this.setText_('instructions', study.getInstructions());
        if (!envs.length) {
            return true;
        }
        // Show the settings for the environment.
        const env = envs[0];
        // Common settings.
        this.setText_('env-id', env.getId());
        this.setText_('env-name', env.getName());
        this.setText_('additional-instructions', env.getAdditionalInstructions());
        this.setText_('max-episode-steps', env.getMaxEpisodeSteps().toString());
        checkCheckbox(this.getId_('sync'), env.getSync());
        const envType = env.getTypeCase();
        checkRadio(this.getId_(StudyEditor.getEnvTypeId_(envType)));
        this.selectEnv_(envType);
        // Environment type specific settings.
        switch (envType) {
            case EnvironmentSpec.TypeCase.PROCGEN: {
                const config = env.getProcgen();
                this.procgenId_.setValue(config.getId());
                this.procgenDistributionMode_.setValue(config.getDistributionMode());
                this.setText_('procgen-num-levels', config.getNumLevels().toString());
                this.setText_('procgen-start-level', config.getStartLevel().toString());
                this.setText_(
                    'procgen-level-repeats', config.getLevelRepeats().toString());
                checkCheckbox(
                    this.getId_('procgen-use-sequential-levels'),
                    config.getUseSequentialLevels());
                break;
            }
            case EnvironmentSpec.TypeCase.ATARI: {
                const config = env.getAtari();
                this.atariId_.setValue(config.getId());
                checkCheckbox(
                    this.getId_('atari-sticky-actions'), config.getStickyActions());
                break;
            }
            case EnvironmentSpec.TypeCase.DMLAB:
                this.dmLabId_.setValue(env.getDmlab().getId());
                break;
            case EnvironmentSpec.TypeCase.NET_HACK:
                this.netHackId_.setValue(env.getNetHack().getId());
                break;
            case EnvironmentSpec.TypeCase.ROBODESK: {
                const config = env.getRobodesk();
                this.robodeskTask_.setValue(config.getTask());
                this.robodeskReward_.setValue(config.getReward());
                this.setText_(
                    'robodesk-action-repeat', config.getActionRepeat().toString());
                this.setText_(
                    'robodesk-image-size', config.getImageSize().toString());
                break;
            }
            case EnvironmentSpec.TypeCase.ROBOSUITE: {
                const config = env.getRobosuite();
                this.robosuiteId_.setValue(config.getId());
                const robots = config.getRobotsList();
                this.robosuiteRobot_.setValue(robots ? robots[0] : '');
                this.robosuiteConfig_.setValue(config.getConfig());
                this.robosuiteArm_.setValue(config.getArm());
                for (const camera of config.getCamerasList()) {
                    checkCheckbox(this.getId_('robosuite-camera-' + camera));
                }
                this.robosuiteController_.setValue(config.getController());
                this.setText_(
                    'robosuite-pos-sensitivity', config.getPosSensitivity().toString());
                this.setText_(
                    'robosuite-rot-sensitivity', config.getRotSensitivity().toString());
                checkCheckbox(
                    this.getId_('robosuite-use-camera-obs'), config.getUseCameraObs());
                break;
            }
        }
        return true;
    }

    /**
     * Returns the study specification as defined in the editor.
     *
     * @return {!StudySpec} Study specification/
     */
    getStudy() {
        const study = new StudySpec()
            .setName(this.getText_('name'))
            .setDescription(this.getText_('description'))
            .setInstructions(this.getText_('instructions'));
        if (this.studyId_) {
            // Setting the ID will update the existing study.
            study.setId(this.studyId_);
        }
        const envType = this.lastEnvType_;
        if (envType != EnvironmentSpec.TypeCase.TYPE_NOT_SET) {
            const env = new EnvironmentSpec()
                .setId(this.getText_('env-id'))
                .setName(this.getText_('env-name'))
                .setAdditionalInstructions(
                    this.getText_('additional-instructions'))
                .setSync(this.isChecked_('sync'));
            study.addEnvironmentSpecs(env);
            this.maybeSetNumber_(
                'max-episode-steps', val => env.setMaxEpisodeSteps(val));
            switch (envType) {
                case EnvironmentSpec.TypeCase.PROCGEN: {
                    const config =
                        new EnvironmentSpec.Procgen()
                        .setId( /** @type {string} */ (this.procgenId_.getValue()))
                        .setDistributionMode( /** @type {!ProcgenDistributionMode} */ (
                            this.procgenDistributionMode_.getValue()))
                        .setUseSequentialLevels(
                            this.isChecked_('procgen-use-sequential-levels'));
                    this.maybeSetNumber_(
                        'procgen-num-levels', val => config.setNumLevels(val));
                    this.maybeSetNumber_(
                        'procgen-start-level', val => config.setStartLevel(val));
                    this.maybeSetNumber_(
                        'procgen-level-repeats', val => config.setLevelRepeats(val));
                    env.setProcgen(config);
                    break;
                }
                case EnvironmentSpec.TypeCase.ATARI:
                    env.setAtari(
                        new EnvironmentSpec.Atari()
                        .setId( /** @type {string} */ (this.atariId_.getValue()))
                        .setStickyActions(this.isChecked_('atari-sticky-actions')));
                    break;
                case EnvironmentSpec.TypeCase.DMLAB:
                    env.setDmlab(new EnvironmentSpec.DMLab().setId(
                        /** @type {string} */
                        (this.dmLabId_.getValue())));
                    break;
                case EnvironmentSpec.TypeCase.NET_HACK:
                    env.setNetHack(new EnvironmentSpec.NetHack().setId(
                        /** @type {string} */
                        (this.netHackId_.getValue())));
                    break;
                case EnvironmentSpec.TypeCase.ROBODESK: {
                    const config = new EnvironmentSpec.RoboDesk().setTask(
                            /** @type {string} */
                            (this.robodeskTask_.getValue()))
                        .setReward( /** @type {!RoboDeskReward} */ (
                            this.robodeskReward_.getValue()));
                    this.maybeSetNumber_(
                        'robodesk-action-repeat', val => config.setActionRepeat(val));
                    this.maybeSetNumber_(
                        'robodesk-image-size', val => config.setImageSize(val));
                    env.setRobodesk(config);
                    break;
                }
                case EnvironmentSpec.TypeCase.ROBOSUITE: {
                    const config =
                        new EnvironmentSpec.Robosuite()
                        .setId( /** @type {string} */ (this.robosuiteId_.getValue()))
                        .addRobots(
                            /** @type {string} */
                            (this.robosuiteRobot_.getValue()))
                        .setConfig(
                            /** @type {string} */
                            (this.robosuiteConfig_.getValue()))
                        .setArm( /** @type {string} */ (this.robosuiteArm_.getValue()))
                        .setController( /** @type {string} */ (
                            this.robosuiteController_.getValue()))
                        .setUseCameraObs(this.isChecked_('robosuite-use-camera-obs'));

                    let cameras = [];
                    for (const camera of this.robosuiteCameras_) {
                        if (this.isChecked_('robosuite-camera-' + camera)) {
                            cameras.push(camera);
                        }
                    }
                    config.setCamerasList(cameras);

                    this.maybeSetFloat_(
                        'robosuite-pos-sensitivity',
                        val => config.setPosSensitivity(val));
                    this.maybeSetFloat_(
                        'robosuite-rot-sensitivity',
                        val => config.setRotSensitivity(val));
                    env.setRobosuite(config);
                    break;
                }
            }
        }
        return study;
    }
}

exports = {
    StudyEditor
};
