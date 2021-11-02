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
 * @fileoverview RLDS Creator application.
 */
goog.module('rlds_creator.app');

const ActionRequest = goog.require('proto.rlds_creator.client.ActionRequest');
const AddEpisodeTagRequest = goog.require('proto.rlds_creator.client.AddEpisodeTagRequest');
const AddEpisodeTagResponse = goog.require('proto.rlds_creator.client.AddEpisodeTagResponse');
const AddStepTagRequest = goog.require('proto.rlds_creator.client.AddStepTagRequest');
const AddStepTagResponse = goog.require('proto.rlds_creator.client.AddStepTagResponse');
const ConfirmSaveResponse = goog.require('proto.rlds_creator.client.ConfirmSaveResponse');
const Data = goog.require('proto.rlds_creator.client.Data');
const DeleteEpisodeRequest = goog.require('proto.rlds_creator.client.DeleteEpisodeRequest');
const DeleteEpisodeResponse = goog.require('proto.rlds_creator.client.DeleteEpisodeResponse');
const DownloadEpisodesRequest = goog.require('proto.rlds_creator.client.DownloadEpisodesRequest');
const DownloadEpisodesResponse = goog.require('proto.rlds_creator.client.DownloadEpisodesResponse');
const EnableStudyRequest = goog.require('proto.rlds_creator.client.EnableStudyRequest');
const EnableStudyResponse = goog.require('proto.rlds_creator.client.EnableStudyResponse');
const EnvironmentSpec = goog.require('proto.rlds_creator.EnvironmentSpec');
const Episode = goog.require('proto.rlds_creator.Episode');
const EpisodeMetadata = goog.require('proto.rlds_creator.client.EpisodeMetadata');
const EpisodeRef = goog.require('proto.rlds_creator.client.EpisodeRef');
const EpisodesResponse = goog.require('proto.rlds_creator.client.EpisodesResponse');
const EventType = goog.require('goog.ui.Component.EventType');
const GamepadInput = goog.require('proto.rlds_creator.client.GamepadInput');
const Html5History = goog.require('goog.history.Html5History');
const OperationRequest = goog.require('proto.rlds_creator.client.OperationRequest');
const OperationResponse = goog.require('proto.rlds_creator.client.OperationResponse');
const Option = goog.require('goog.ui.Option');
const PauseResponse = goog.require('proto.rlds_creator.client.PauseResponse');
const RemoveEpisodeTagRequest = goog.require('proto.rlds_creator.client.RemoveEpisodeTagRequest');
const RemoveEpisodeTagResponse = goog.require('proto.rlds_creator.client.RemoveEpisodeTagResponse');
const RemoveStepTagRequest = goog.require('proto.rlds_creator.client.RemoveStepTagRequest');
const RemoveStepTagResponse = goog.require('proto.rlds_creator.client.RemoveStepTagResponse');
const ReplayEpisodeRequest = goog.require('proto.rlds_creator.client.ReplayEpisodeRequest');
const ReplayEpisodeResponse = goog.require('proto.rlds_creator.client.ReplayEpisodeResponse');
const ReplayStepRequest = goog.require('proto.rlds_creator.client.ReplayStepRequest');
const ReplayStepResponse = goog.require('proto.rlds_creator.client.ReplayStepResponse');
const SaveEpisodeRequest = goog.require('proto.rlds_creator.client.SaveEpisodeRequest');
const SaveEpisodeResponse = goog.require('proto.rlds_creator.client.SaveEpisodeResponse');
const SaveStudyRequest = goog.require('proto.rlds_creator.client.SaveStudyRequest');
const Select = goog.require('goog.ui.Select');
const SelectEnvironmentRequest = goog.require('proto.rlds_creator.client.SelectEnvironmentRequest');
const SelectEnvironmentResponse = goog.require('proto.rlds_creator.client.SelectEnvironmentResponse');
const SelectStudyRequest = goog.require('proto.rlds_creator.client.SelectStudyRequest');
const SelectStudyResponse = goog.require('proto.rlds_creator.client.SelectStudyResponse');
const SetCameraRequest = goog.require('proto.rlds_creator.client.SetCameraRequest');
const SetCameraResponse = goog.require('proto.rlds_creator.client.SetCameraResponse');
const SetFpsRequest = goog.require('proto.rlds_creator.client.SetFpsRequest');
const SetQualityRequest = goog.require('proto.rlds_creator.client.SetQualityRequest');
const SetStudiesRequest = goog.require('proto.rlds_creator.client.SetStudiesRequest');
const SetStudiesResponse = goog.require('proto.rlds_creator.client.SetStudiesResponse');
const StepResponse = goog.require('proto.rlds_creator.client.StepResponse');
const StudySpec = goog.require('proto.rlds_creator.StudySpec');
const TableSorter = goog.require('goog.ui.TableSorter');
const UpdateReplayEpisodeRequest = goog.require('proto.rlds_creator.client.UpdateReplayEpisodeRequest');
const UpdateReplayEpisodeResponse = goog.require('proto.rlds_creator.client.UpdateReplayEpisodeResponse');
const Uri = goog.require('goog.Uri');
const classlist = goog.require('goog.dom.classlist');
const dataset = goog.require('goog.dom.dataset');
const dom = goog.require('goog.dom');
const events = goog.require('goog.events');
const style = goog.require('goog.style');
const {ConfirmDialog} = goog.require('rlds_creator.confirmDialog');
const {StudyEditor} = goog.require('rlds_creator.studyEditor');
const {checkCheckbox, createIcon, createNonNumericCell, createNumericCell, createSelect, createSwitch, getElement, hideElement, isChecked, setTextContent, setTextField, showElement} = goog.require('rlds_creator.utils');

const Quality = SetQualityRequest.Quality;

/**
 * Returns the URI for replaying an episode.
 *
 * @param {!Episode} episode Episode.
 * @return {!Uri} an URI of the form replay?study=...&session=...&episode=...
 */
function getReplayUri(episode) {
  return new Uri()
      .setPath('replay')
      .setParameterValue('study', episode.getStudyId())
      .setParameterValue('session', episode.getSessionId())
      .setParameterValue('episode', episode.getId());
}

/**
 * Returns the URI for a study.
 *
 * @param {string} studyId ID of the study.
 * @return {!Uri} an URI of the form study?id=...
 */
function getStudyUri(studyId) {
  return new Uri().setPath('study').setParameterValue('id', studyId);
}

/**
 * Returns the URI for an environment of a study.
 *
 * @param {string} studyId ID of the study.
 * @param {string} envId ID of the environment.
 * @return {!Uri} an URI of the form env?study=...&id=...
 */
function getEnvUri(studyId, envId) {
  return new Uri()
      .setPath('env')
      .setParameterValue('study', studyId)
      .setParameterValue('id', envId);
}

/**
 * Sets the href of an anchor element to the URI as a fragment.
 *
 * @param {!HTMLAnchorElement} anchor The anchor element.
 * @param {!Uri} uri URI that will be assigned to the href property.
 */
function setHref(anchor, uri) {
  dom.safe.setAnchorHref(anchor, '#' + uri.toString());
}

/**
 * Switches to the tab with the specified ID.
 *
 * @param {string} id
 */
function switchToTab(id) {
  dom.getElement(id).dispatchEvent(new Event(events.EventType.CLICK));
}

/**
 * Displays the encoded image in the canvas.
 *
 * @param {?HTMLCanvasElement} canvas A canvas.
 * @param {!Uint8Array} encoded_image An encoded image.
 */
function displayImage(canvas, encoded_image) {
  if (!canvas) {
    return;
  }
  const ctx = dom.getCanvasContext2D(canvas);
  createImageBitmap(new Blob([encoded_image])).then(function(img) {
    // Scale the image to fit the (square) canvas.
    const s = img.width / img.height;
    let w = canvas.width;
    let h = canvas.height;
    if (img.width > img.height) {
      h = Math.round(w / s);
    } else {
      w = Math.round(h * s);
    }
    ctx.drawImage(img, 0, 0, w, h);
  });
}

/**
 * The application.
 * @abstract
 */
class App {
  /**
   * Event handler for the keydown event on the canvas.
   *
   * @param {!Event} e A keydown event.
   * @private
   */
  handleKeyDown_(e) {
    const keyboardEvent = /** @type {!KeyboardEvent} */ (e);
    if (!keyboardEvent.repeat) {
      const key = keyboardEvent.key;
      // Check the camera keys, i.e. 1 to 9.
      const ord = key.charCodeAt(0);
      if (ord >= 49 && ord <= 57) {
        // Camera index is 0-based.
        this.sendRequest(new OperationRequest().setSetCamera(
            new SetCameraRequest().setIndex(ord - 49)));
        return;
      }
      this.pressedKeys_.add(key);
      this.sendKeys_();
    }
    e.preventDefault();
    e.stopPropagation();
  }

  /**
   * Event handler for the keyup event on the canvas.
   *
   * @param {!Event} e A keyup event.
   * @private
   */
  handleKeyUp_(e) {
    const keyboardEvent = /** @type {!KeyboardEvent} */ (e);
    if (!keyboardEvent.repeat) {
      this.pressedKeys_.delete(keyboardEvent.key);
      this.sendKeys_();
    }
    e.preventDefault();
    e.stopPropagation();
  }

  /**
   * Returns true if connected to the server.
   * @return {boolean}
   * @abstract
   */
  isConnected() {}

  /**
   * Send the keys that are currently pressed.
   * @private
   */
  sendKeys_() {
    if (!this.isConnected() || !this.currentEnv_) {
      return;
    }
    if (this.pressedKeys_.has('/')) {
      this.setBusy_();
    }
    const actionRequest =
        new ActionRequest().setKeysList(Array.from(this.pressedKeys_));
    // We support a single gamepad controller.
    const gamepad = this.gamepadControllers_.values().next().value;
    if (gamepad) {
      const gamepadInput = new GamepadInput().setId(gamepad.id);
      gamepad.buttons.forEach(function(button, index) {
        if (button.pressed || button.value > 0) {
          gamepadInput.getButtonsMap().set(
              index,
              new GamepadInput.Button()
                  .setPressed(button.pressed)
                  .setValue(button.value));
        }
      });
      gamepad.axes.forEach(function(value, index) {
        if (value != 0) {
          gamepadInput.getAxesMap().set(index, value);
        }
      });
      actionRequest.setGamepadInput(gamepadInput);
    }
    this.sendRequest(new OperationRequest().setAction(actionRequest));
  }

  /**
   * Sets the busy state. This will show or hide the overlay.
   *
   * @param {boolean=} busy Whether the busy state is enabled or not.
   * @private
   */
  setBusy_(busy = true) {
    showElement('busy-overlay', busy);
  }

  /**
   * Sends the specified operation request.
   *
   * @param {!OperationRequest} request Operation request.
   * @abstract @protected
   */
  sendRequest(request) {}

  /**
   * Shows a message in the snackbar.
   *
   * @param {string} message The message to display.
   * @param {number=} duration Duration in msecs to display the message.
   * @private
   */
  showMessage_(message, duration = 3000) {
    this.snackBar_.MaterialSnackbar.showSnackbar(
        {message: message, timeout: duration});
  }

  /**
   * Shows an error message in the snackbar.
   *
   * @param {string} message The error message to display.
   * @protected
   */
  showError(message) {
    // Display for 5 seconds.
    this.showMessage_(message, 5000);
    this.setBusy_(false);
    // The download dialog may be open when the error has occurred.
    if (this.downloadDialog_.open) {
      this.downloadDialog_.close();
    }
  }

  /**
   * Sets the URI of the current page.
   *
   * @param {!Uri} uri an URI to set as the history token.
   * @private
   */
  setPageUri_(uri) {
    this.history_.setToken(uri.toString());
  }

  /**
   * Returns true if the invalid episodes can be shown in the episodes tab.
   *
   * @return {boolean}
   * @private
   */
  canShowInvalidEpisodes_() {
    return !isChecked('status-valid');
  }

  /**
   * Adds a new episode to the episodes table.
   *
   * @param {!EpisodeMetadata} episodeMetadata Episode metadata.
   * @param {number=} index Index of the row to insert. -1 indicates last row.
   * @private
   */
  addEpisode_(episodeMetadata, index = -1) {
    if (!this.episodesTbl_ || !episodeMetadata) {
      return;
    }
    const row =
        /** @type {!HTMLElement} */ (
            this.episodesTbl_.tBodies[0].insertRow(index));
    // Attach the study, session and episode IDs to the row data. These are
    // later used for applying an operation to selected episodes.
    const episode = episodeMetadata.getEpisode();
    const studyId = episode.getStudyId();
    const sessionId = episode.getSessionId();
    dataset.set(row, 'study', studyId);
    dataset.set(row, 'session', sessionId);
    dataset.set(row, 'episode', episode.getId());
    if (episode.getState() != Episode.State.STATE_COMPLETED) {
      classlist.add(row, 'invalid');
      style.setElementShown(row, this.canShowInvalidEpisodes_());
    }
    const episodeId = dom.createDom(
        dom.TagName.A, {'title': 'Replay the episode'}, episode.getId());
    setHref(episodeId, getReplayUri(episode));
    events.listen(episodeId, events.EventType.CLICK, e => {
      this.requestReplayEpisode_(studyId, sessionId, episode.getId());
      e.preventDefault();
    });
    // Include both the episode and step tags.
    let tags = new Set();
    episode.getTagsList().forEach(function(tag) {
      tags.add(tag.getLabel());
    });
    for (const [index, stepMetadata] of episode.getStepMetadataMap()
             .entries()) {
      for (const tag of stepMetadata.getTagsList()) {
        tags.add(tag.getLabel());
      }
    }
    dom.append(
        row,
        dom.createDom(
            dom.TagName.TD, null,
            /** @type {!MDLDataTableElement} */
            (this.episodesTbl_).MaterialDataTable.createCheckbox_(row)),
        createNonNumericCell(episode.getStartTime().toDate().toUTCString()),
        createNonNumericCell(episodeMetadata.getEnv().getName()),
        createNonNumericCell(episode.getSessionId()),
        createNonNumericCell(episodeId),
        createNonNumericCell(episodeMetadata.getStatus()),
        createNonNumericCell(Array.from(tags).join(', ')),
        createNumericCell(episode.getNumSteps()),
        createNumericCell(episode.getTotalReward()),
        createNonNumericCell(episodeMetadata.getDuration()));
    const actions = dom.createDom(dom.TagName.DIV);
    const replayButton = dom.createDom(
        dom.TagName.BUTTON, {
          'class': 'mdl-button mdl-js-button mdl-button--icon',
          'title': 'Replay the episode'
        },
        createIcon('replay'));
    events.listen(
        replayButton, events.EventType.CLICK,
        e => this.requestReplayEpisode_(studyId, sessionId, episode.getId()));
    dom.appendChild(actions, replayButton);
    // Add the delete button if the operation is possible.
    if (episodeMetadata.getCanDelete()) {
      const deleteButton = dom.createDom(
          dom.TagName.BUTTON, {
            'class': 'mdl-button mdl-js-button mdl-button--icon',
            'title': 'Delete episode'
          },
          createIcon('delete'));
      events.listen(deleteButton, events.EventType.CLICK, e => {
        new ConfirmDialog(
            'Delete the episode? This is an irreversible operation.')
            .showModal(accept => {
              if (accept) {
                this.requestDeleteEpisode_(studyId, sessionId, episode.getId());
              }
              return true;
            });
      });
      dom.appendChild(actions, deleteButton);
      if (episodeMetadata.hasVideoUrl()) {
        const video = dom.createDom(
            dom.TagName.A, {
              'target': '_blank',
              'class': 'mdl-button mdl-js-button mdl-button--icon',
              'title': 'Video of the episode'
            },
            createIcon('movie'));
        dom.safe.setAnchorHref(video, episodeMetadata.getVideoUrl());
        dom.appendChild(actions, video);
      }
    }
    dom.append(row, createNonNumericCell(actions));
  }

  /**
   * Makes a request to delete the specified episode.
   *
   * @param {string} studyId ID of the study.
   * @param {string} sessionId ID of the session.
   * @param {string} episodeId ID of the episode.
   * @private
   */
  requestDeleteEpisode_(studyId, sessionId, episodeId) {
    this.setBusy_();
    const ref = new EpisodeRef()
                    .setStudyId(studyId)
                    .setSessionId(sessionId)
                    .setEpisodeId(episodeId);
    this.sendRequest(new OperationRequest().setDeleteEpisode(
        new DeleteEpisodeRequest().setRef(ref)));
  }

  /**
   * Removes the episode from the episodes table if the delete operation was
   * successful.
   *
   * @param {!DeleteEpisodeResponse} response Response for the delete episode
   *     request.
   * @private
   */
  deleteEpisode_(response) {
    this.setBusy_(false);
    if (!response.getSuccess()) {
      this.showError('Unable to delete the episode.');
      return;
    }
    const ref = response.getRef();
    // TODO(sertan): Use querySelector to find the episode row.
    const body = this.episodesTbl_.tBodies[0];
    const rows = body.rows;
    for (let i = 0, n = rows.length; i < n; ++i) {
      const row = rows[i];
      if (dataset.get(row, 'study') == ref.getStudyId() &&
          dataset.get(row, 'session') == ref.getSessionId() &&
          dataset.get(row, 'episode') == ref.getEpisodeId()) {
        body.deleteRow(row.sectionRowIndex);
        return;
      }
    }
  }

  /**
   * Makes a request to replay the specified episode.
   *
   * @param {string} studyId ID of the study.
   * @param {string} sessionId ID of the session.
   * @param {string} episodeId ID of the episode.
   * @private
   */
  requestReplayEpisode_(studyId, sessionId, episodeId) {
    this.setBusy_();
    this.sendRequest(new OperationRequest().setReplayEpisode(
        new ReplayEpisodeRequest().setRef(new EpisodeRef()
                                              .setStudyId(studyId)
                                              .setSessionId(sessionId)
                                              .setEpisodeId(episodeId))));
  }

  /**
   * Requests the step with the specified index to replay.
   *
   * @param {number} index 0-based index of the step.
   * @private
   */
  requestReplayStep_(index) {
    if (this.currentReplay_ && this.currentReplayIndex_ != index) {
      this.sendRequest(new OperationRequest().setReplayStep(
          new ReplayStepRequest().setIndex(index)));
    }
  }

  /**
   * Updates the reward chart.
   */
  updateRewardChart_() {
    // Thee are two series, i.e. reward and the cumulative reward. We maximize
    // the chart area and hide the legend. Crosshair provides the visual clue
    // for the current step of the replay.
    this.replayRewardChart_.draw(
        /** @type{!Object} */ (this.replayRewardData_), {
          'crosshair': {'trigger': 'both', 'color': '#2471A3'},
          'height': 400,
          'legend': {'position': 'none'},
          'series': {0: {'targetAxisIndex': 0}, 1: {'targetAxisIndex': 1}},
          'theme': 'maximized',
          'width': 600,
        });
    // Focus on the current step.
    this.replayRewardChart_.setSelection(
        [{'row': this.currentReplayIndex_, 'column': 1}]);
  }

  /**
   * Sets the episode to replay.
   *
   * @param {!ReplayEpisodeResponse} response Response for the replay episode
   * request.
   * @private
   */
  setReplayEpisode_(response) {
    hideElement('replay-intro');
    // Clear the replay canvas.
    if (this.replayCanvas_) {
      const ctx = dom.getCanvasContext2D(this.replayCanvas_);
      ctx.clearRect(0, 0, this.replayCanvas_.width, this.replayCanvas_.height);
    }
    this.currentReplayIndex_ = -1;
    const episodeMetadata = response.getEpisode();
    if (!episodeMetadata || !episodeMetadata.hasEpisode()) {
      this.currentReplay_ = null;
      return;
    }
    const episode = episodeMetadata.getEpisode();
    this.currentReplay_ = episode;
    // Request the first step of the episode.
    this.requestReplayStep_(0);
    // Make the replay container visible and populate the metadata.
    showElement('replay-container');
    setTextContent('replay-study-name', episodeMetadata.getStudy().getName());
    setTextContent('replay-env-name', episodeMetadata.getEnv().getName());
    setTextContent(
        'replay-start-time', episode.getStartTime().toDate().toUTCString());
    setTextContent('replay-id', episode.getId());
    setTextContent('replay-step', '-');
    const numSteps = episode.getNumSteps();
    setTextContent('replay-num-steps', numSteps);
    this.replayStepSlider_.setAttribute('max', numSteps > 0 ? numSteps : 0);
    this.replayStepSlider_.MaterialSlider.change(0);
    setTextContent('replay-total-reward', episode.getTotalReward());
    setTextField('replay-episode-notes', episode.getNotes());
    // Remove the existing episode tag chips.
    dom.removeChildren(dom.getElement('replay-episode-tags'));
    this.episodeTagChips_ = {};
    for (const tag of episode.getTagsList()) {
      this.addEpisodeTagChip_(tag.getLabel());
    }
    // Remove the existing step tag chips. These will be populated when
    // rendering a replay step.
    dom.removeChildren(dom.getElement('replay-step-tags'));
    this.stepTagChips_ = {};

    // Create the timeseries data for the step rewards.
    const stepRewards = response.getStepRewardsList();
    // The column names in the header is also used in the tooltips.
    let rewardSeries = [[
      'step', 'reward', {'type': 'string', 'role': 'annotation'}, 'total reward'
    ]];
    let sum = 0;
    stepRewards.forEach(function(reward, index) {
      sum += reward;
      rewardSeries.push([index, reward, null, sum]);
    });
    this.replayRewardData_ =
        google.visualization.arrayToDataTable(rewardSeries);

    // Add the step tags to the reward chart.
    this.stepTagAnnotations_.clear();
    for (const [index, stepMetadata] of episode.getStepMetadataMap()
             .entries()) {
      if (!stepMetadata) {
        continue;
      }
      let tags = [];
      for (const tag of stepMetadata.getTagsList()) {
        tags.push(tag.getLabel());
      }
      if (tags.length) {
        this.stepTagAnnotations_.set(index, new Set(tags));
        this.replayRewardData_.setCell(
            /** @type{number} */ (index), 2, tags.join());
      }
    }
    this.updateRewardChart_();

    switchToTab('replay-tab');
    this.setBusy_(false);
    this.replayCanvas_.focus();
    this.setPageUri_(getReplayUri(episode));
  }

  /**
   * Displays the replay data.
   *
   * @param {?Data} data
   * @param {?Element} parentEl Parent element to display the data.
   * @private
   */
  displayData_(data, parentEl) {
    if (!parentEl) {
      return;
    }
    dom.removeChildren(parentEl);
    if (!data) {
      return;
    }
    switch (data.getTypeCase()) {
      case Data.TypeCase.JSON_ENCODED: {
        const obj = JSON.parse(data.getJsonEncoded());
        const simplified = isChecked('replay-simplified');
        dom.appendChild(
            parentEl,
            dom.createDom(
                dom.TagName.PRE, {}, JSON.stringify(obj, function(key, val) {
                  return simplified && (typeof val === 'number') ?
                      Number(val.toFixed(3)) :
                      val;
                }, 2)));
        break;
      }
    }
    // Display images if any.
    data.getImagesList().forEach(function(image) {
      const imgContainer = dom.createDom(
          dom.TagName.DIV, {'class': 'data-image'}, image.getName());
      const img = new Image();
      img.src = 'data:image/png;base64,' + image.getImage();
      dom.appendChild(imgContainer, img);
      dom.appendChild(parentEl, imgContainer);
    });
  }

  /**
   * Replays the step.
   *
   * @param {!ReplayStepResponse} response Response for the replay step request.
   * @private
   */
  replayStep_(response) {
    const index = response.getIndex();
    this.currentReplayIndex_ = index;
    this.replayStepSlider_.MaterialSlider.change(index);
    setTextContent('replay-step', index + 1);
    setTextContent('replay-keys', response.getKeysList().join(', '));
    const reward = response.hasReward() ? response.getReward() : '(none)';
    setTextContent('replay-reward', reward);
    displayImage(this.replayCanvas_, response.getImage_asU8());
    this.displayData_(
        response.getObservation(), dom.getElement('replay-observation'));
    this.displayData_(response.getAction(), dom.getElement('replay-action'));
    // Remove the existing tags and add the current ones, if any.
    dom.removeChildren(dom.getElement('replay-step-tags'));
    this.stepTagChips_ = {};
    for (const tag of response.getTagsList()) {
      this.addStepTagChip_(index, tag);
    }
    // Select the point in the reward chart.
    this.replayRewardChart_.setSelection([{'row': index, 'column': 1}]);
  }

  /**
   * Handles the event to change the replay step by the specified offset.
   *
   * @param {number} offset Offset to add to the current step.
   * @private
   */
  handleReplayStep_(offset) {
    if (!this.currentReplay_) {
      return;
    }
    const index = this.currentReplayIndex_ + offset;
    if (index >= 0 && index <= this.currentReplay_.getNumSteps()) {
      this.requestReplayStep_(index);
    }
  }

  /**
   * Event handler for the keypress event on the replay canvas.
   *
   * @param {!Event} e A keypress event.
   * @private
   */
  handleReplayKeyDown_(e) {
    const keyboardEvent = /** @type {!KeyboardEvent} */ (e);
    const offset = keyboardEvent.shiftKey ? 10 : 1;
    switch (keyboardEvent.key) {
      case 'ArrowLeft':
        this.handleReplayStep_(-offset);
        break;
      case 'ArrowRight':
        this.handleReplayStep_(offset);
        break;
    }
    e.preventDefault();
  }

  /**
   * Adds a new tag.
   *
   * @param {string} tag Tag.
   * @param {!Element} parentEl Parent element that the chip will be added.
   * @param {?Function} deleteCallback Function that will be called with the tag
   * when the delete button is clicked.
   * @return {!Element} a chip element.
   * @private
   */
  addTagChip_(tag, parentEl, deleteCallback) {
    const chip = dom.createDom(
        dom.TagName.SPAN, {'class': 'replay-tag mdl-chip mdl-chip--deletable'});
    const deleteButton = dom.createDom(
        dom.TagName.BUTTON, {'class': 'mdl-chip__action'},
        createIcon('cancel'));
    events.listen(deleteButton, events.EventType.CLICK, function(e) {
      if (deleteCallback) {
        deleteCallback(tag);
      }
    });
    dom.append(
        chip, dom.createDom(dom.TagName.SPAN, {'class': 'mdl-chip__text'}, tag),
        deleteButton);
    dom.append(parentEl, chip);
    return chip;
  }

  /**
   * Handles the event to add a tag for the episode.
   *
   * @param {!Event} e A change event.
   * @private
   */
  handleAddEpisodeTag_(e) {
    const el = /** @type {!HTMLInputElement} */ (e.target);
    const tag = el.value;
    // Clear the entered value.
    el.value = '';
    if (tag) {
      this.sendRequest(new OperationRequest().setAddEpisodeTag(
          new AddEpisodeTagRequest().setTag(tag)));
    }
  }

  /**
   * Adds an epsiode tag chip.
   *
   * @param {string} tag Label of the tag.
   * @private
   */
  addEpisodeTagChip_(tag) {
    this.episodeTagChips_[tag] = this.addTagChip_(
        tag, /** @type {!Element} */ (dom.getElement('replay-episode-tags')),
        tag => this.sendRequest(new OperationRequest().setRemoveEpisodeTag(
            new RemoveEpisodeTagRequest().setTag(tag))));
  }

  /**
   * Adds an episode tag.
   *
   * @param {!AddEpisodeTagResponse} response Response for the add episode tag
   *     request.
   * @private
   */
  addEpisodeTag_(response) {
    const tag = response.getTag();
    if (response.getSuccess()) {
      this.addEpisodeTagChip_(tag);
    } else {
      this.showError(`Unable to add "${tag}" tag for the episode.`);
    }
  }

  /**
   * Removes an episode tag.
   *
   * @param {!RemoveEpisodeTagResponse} response Response for the remove episode
   *     tag request.
   * @private
   */
  removeEpisodeTag_(response) {
    const tag = response.getTag();
    if (response.getSuccess()) {
      // Remove the chip of the tag.
      const chip = this.episodeTagChips_[tag];
      if (chip) {
        dom.removeNode(chip);
        delete this.episodeTagChips_[tag];
      }
    } else {
      this.showError(`Unable to remove "${tag}" tag for the episode.`);
    }
  }

  /**
   * Handles the event to add a tag for the current step of the episode.
   *
   * @param {!Event} e A change event.
   * @private
   */
  handleAddStepTag_(e) {
    const el = /** @type {!HTMLInputElement} */ (e.target);
    const tag = el.value;
    // Clear the entered value.
    el.value = '';
    if (tag) {
      this.sendRequest(new OperationRequest().setAddStepTag(
          new AddStepTagRequest()
              .setIndex(this.currentReplayIndex_)
              .setTag(tag)));
    }
  }

  /**
   * Adds a step tag chip.
   *
   * @param {number} index Index of the step.
   * @param {string} tag Label of the tag.
   * @private
   */
  addStepTagChip_(index, tag) {
    this.stepTagChips_[tag] = this.addTagChip_(
        tag, /** @type {!Element} */ (dom.getElement('replay-step-tags')),
        tag => this.sendRequest(new OperationRequest().setRemoveStepTag(
            new RemoveStepTagRequest().setIndex(index).setTag(tag))));
  }

  /**
   * Updates the tags of a step on the reward chart.
   *
   * @param {number} index Index of the step.
   * @private
   */
  updateStepTags_(index) {
    const tags = this.stepTagAnnotations_.get(index);
    let annotation = null;
    if (tags !== undefined && tags.size > 0) {
      annotation = Array.from(tags).join();
    }
    this.replayRewardData_.setCell(index, 2, annotation);
    this.updateRewardChart_();
  }

  /**
   * Adds a step tag.
   *
   * @param {!AddStepTagResponse} response Response for the add step tag
   *     request.
   * @private
   */
  addStepTag_(response) {
    const tag = response.getTag();
    if (response.getSuccess()) {
      const index = response.getIndex();
      if (index == this.currentReplayIndex_) {
        this.addStepTagChip_(index, tag);
      }
      // Add the tag to the reward chart.
      let tags = this.stepTagAnnotations_.get(index);
      if (tags == undefined) {
        tags = new Set();
        this.stepTagAnnotations_.set(index, tags);
      }
      tags.add(tag);
      this.updateStepTags_(index);
    } else {
      this.showError(`Unable to add "${tag}" tag for the step.`);
    }
  }

  /**
   * Removes a step tag.
   *
   * @param {!RemoveStepTagResponse} response Response for the remove step tag
   *     request.
   * @private
   */
  removeStepTag_(response) {
    const tag = response.getTag();
    if (response.getSuccess()) {
      const index = response.getIndex();
      if (index == this.currentReplayIndex_) {
        // Remove the chip of the tag.
        const chip = this.stepTagChips_[tag];
        if (chip) {
          dom.removeNode(chip);
          delete this.stepTagChips_[tag];
        }
      }
      // Remove the tag from the reward chart.
      const tags = this.stepTagAnnotations_.get(index);
      if (tags !== undefined) {
        tags.delete(tag);
        this.updateStepTags_(index);
      }
    } else {
      this.showError(`Unable to remove "${tag}" tag for the step.`);
    }
  }

  /**
   * Handles the event to update an episode.
   * @private
   */
  handleUpdateEpisode_() {
    const notes = /** @type {!HTMLTextAreaElement} */ (
        dom.getElement('replay-episode-notes'));
    this.sendRequest(new OperationRequest().setUpdateReplayEpisode(
        new UpdateReplayEpisodeRequest().setNotes(notes.value)));
  }

  /**
   * Handles the event to download episodes.
   * @private
   */
  handleDownloadEpisodes_() {
    const rows = dom.getElementsByTagNameAndClass(
        dom.TagName.TR, 'is-selected', this.episodesTbl_);
    if (!rows) {
      // No episodes to download.
      return;
    }
    dom.removeChildren(dom.getElement('download-link'));
    const request = new DownloadEpisodesRequest();
    for (let i = 0, n = rows.length; i < n; ++i) {
      const row = rows[i];
      request.addRefs(
          new EpisodeRef()
              .setStudyId(/** @type {string} */ (dataset.get(row, 'study')))
              .setSessionId(/** @type {string} */ (dataset.get(row, 'session')))
              .setEpisodeId(
                  /** @type {string} */ (dataset.get(row, 'episode'))));
    }
    const tags =
        /** @type {!HTMLInputElement} */ (dom.getElement('end_of_episode_tags'))
            .value;
    request.setArchive(isChecked('download-archive'))
        .setStripInternalMetadata(!isChecked('download-keep-internal-metadata'))
        .setEndOfEpisodeTagsList(tags.split(',')
                                     .map(tag => tag.trim())
                                     .filter(tag => tag.length > 0));
    this.downloadProgress_.MaterialProgress.setProgress(0);
    // To visually indicate that the request is being processed.
    this.downloadProgress_.MaterialProgress.setBuffer(87);
    showElement(this.downloadProgress_);
    hideElement('download-link-container');
    // TODO(sertan): Add support for cancalling the operation. Currently, we
    // hide the buttons.
    hideElement('download-actions');
    this.downloadDialog_.showModal();
    this.sendRequest(new OperationRequest().setDownloadEpisodes(request));
  }

  /**
   * Updates the download progress. It will display the link to download the
   * selected episodes when the dataset is ready.
   *
   * @param {!DownloadEpisodesResponse} response Response for the download
   *     episodes request.
   * @private
   */
  setDownloadProgress_(response) {
    const url = response.getUrl();
    if (!url) {
      // The dataset is not ready yet, only update the progress.
      this.downloadProgress_.MaterialProgress.setProgress(
          response.getProgress());
      return;
    }
    const anchor = dom.createDom(dom.TagName.A, {'target': 'blank_'}, url);
    dom.safe.setAnchorHref(anchor, url);
    dom.appendChild(dom.getElement('download-link'), anchor);
    hideElement(this.downloadProgress_);
    showElement('download-link-container');
    showElement('download-actions');
  }

  /**
   * Adds the list of studies to the select box.
   *
   * @param {!Array<!StudySpec>} studies List of studies.
   * @private
   */
  addStudiesToSelect_(studies) {
    const existingIds = new Set();
    for (let i = 0, n = this.selectStudy_.getItemCount(); i < n; ++i) {
      existingIds.add(this.selectStudy_.getItemAt(i).getValue());
    }
    for (const study of studies) {
      if (!existingIds.has(study.getId())) {
        this.selectStudy_.addItem(new Option(study.getName(), study.getId()));
      }
    }
    this.selectStudy_.setEnabled(this.selectStudy_.getItemCount() > 0);
  }

  /**
   * Sets the current study.
   *
   * @param {!SelectStudyResponse} response Response for the select study
   *     request.
   * @private
   */
  setStudy_(response) {
    const study = /** @type {!StudySpec} */ (response.getStudy());
    this.addStudiesToSelect_([study]);
    const studyId = study.getId();
    this.selectStudy_.setValue(studyId);
    // Populate environments of the study.
    for (const env of study.getEnvironmentSpecsList()) {
      this.selectEnv_.addItem(new Option(env.getName(), env.getId()));
    }
    this.selectEnv_.setEnabled(true);
    setTextContent('study-description', study.getDescription());
    setTextContent('study-instructions', study.getInstructions());
    // Clear the list of episodes.
    if (this.episodesTbl_) {
      dom.removeChildren(this.episodesTbl_.tBodies[0]);
    }
    showElement('episodes-loading');
    hideElement('episodes-container');
    if (this.envToLoad_) {
      this.selectEnv_.setValue(this.envToLoad_);
      if (this.selectEnv_.getValue()) {
        this.requestSelectEnvironment_(this.envToLoad_);
        this.envToLoad_ = null;
        return;
      }
      this.showError('Invalid environment.');
    }
    this.setBusy_(false);
    this.setPageUri_(getStudyUri(studyId));
    switchToTab('episodes-tab');
  }

  /**
   * Sets the current environment.
   *
   * @param {!SelectEnvironmentResponse} response Response for the select
   * environment request.
   * @private
   */
  setEnvironment_(response) {
    const env = /** @type {!EnvironmentSpec} */ (response.getEnv());
    this.currentEnv_ = env;
    hideElement('env-intro');
    hideElement('env-camera');
    setTextContent(
        'env-instructions', env.getAdditionalInstructions() || 'None.');
    // Show the environment container and focus on the canvas.
    showElement('env-container');
    const fps = dom.getElement('fps-slider');
    if (env.getSync()) {
      fps.setAttribute('disabled', '');
    } else {
      fps.removeAttribute('disabled');
    }
    switchToTab('player-tab');
    if (this.canvas_) {
      this.canvas_.focus();
    }
    this.setBusy_(false);
    this.setPageUri_(getEnvUri(response.getStudyId(), env.getId()));
  }

  /**
   * Sets the episodes, i.e. populates the episodes tab.
   *
   * @param {!EpisodesResponse} response Response for the episodes request.
   * @private
   */
  setEpisodes_(response) {
    const episodes = response.getEpisodesList();
    hideElement('episodes-loading');
    if (episodes && episodes.length > 0) {
      showElement('episodes-container');
      for (const episode of episodes) {
        this.addEpisode_(episode);
      }
    }
  }

  /**
   * Makes a request to select the specified study.
   *
   * @param {string} id ID of the study.
   * @private
   */
  requestSelectStudy_(id) {
    this.setBusy_();
    hideElement('env-container');
    showElement('env-intro');
    this.currentEnv_ = null;
    // Clear the list of environments and hide the environment container.
    while (this.selectEnv_.getItemCount()) {
      this.selectEnv_.removeItemAt(0);
    }
    this.selectEnv_.setEnabled(false);
    this.sendRequest(new OperationRequest().setSelectStudy(
        new SelectStudyRequest().setStudyId(id)));
  }

  /**
   * Makes a request to select the specified environment.
   *
   * @param {string} id ID of the environment.
   * @private
   */
  requestSelectEnvironment_(id) {
    this.setBusy_();
    // Clear the canvas.
    if (this.canvas_) {
      dom.getCanvasContext2D(this.canvas_)
          .clearRect(0, 0, this.canvas_.width, this.canvas_.height);
    }
    this.sendRequest(new OperationRequest().setSelectEnvironment(
        new SelectEnvironmentRequest().setEnvId(id)));
  }

  /**
   * Populates the list of studies.
   *
   * @param {!SetStudiesResponse} response Response for the set studies request.
   * @private
   */
  setStudies_(response) {
    this.setBusy_(false);
    const studies = response.getStudiesList();
    if (!studies.length || !this.studiesTbl_) {
      // Nothing to display.
      hideElement('studies-container');
      showElement('studies-intro');
      return;
    }
    const body = this.studiesTbl_.tBodies[0];
    // Delete existing studies.
    dom.removeChildren(body);
    // Update the selection box.
    this.addStudiesToSelect_(studies);
    // Populate the table with the studies.
    for (const study of studies) {
      const row = /** @type {!HTMLElement} */ (body.insertRow());
      const id = study.getId();
      const studyName = dom.createDom(
          dom.TagName.A, {'title': 'List recorded episodes'}, study.getName());
      setHref(studyName, getStudyUri(id));
      events.listen(studyName, events.EventType.CLICK, e => {
        this.requestSelectStudy_(id);
        switchToTab('episodes-tab');
        e.preventDefault();
      });
      // Clicking on the edit icon will show the study editor.
      const edit = dom.createDom(
          dom.TagName.BUTTON, {
            'class': 'mdl-button mdl-js-button mdl-button--icon',
            'title': 'Edit study'
          },
          createIcon('edit'));
      events.listen(edit, events.EventType.CLICK, e => {
        if (this.studyEditor_ && this.studyEditor_.setStudy(study)) {
          this.showStudyEditor_();
        }
      });
      const enabledId = 'enabled-' + study.getId();
      const enabled = createSwitch(
          enabledId, study.getState() == StudySpec.State.STATE_ENABLED);
      componentHandler.upgradeElement(enabled);
      events.listen(enabled, events.EventType.CLICK, e => {
        this.setBusy_();
        // Invert the check state.
        const enable = !isChecked(enabledId);
        this.sendRequest(
            new OperationRequest().setEnableStudy(new EnableStudyRequest()
                                                      .setStudyId(study.getId())
                                                      .setEnable(enable)));
        // The state of the switch will be updated asynchronously based on the
        // response.
        e.preventDefault();
      });
      const envsContainer =
          dom.createDom(dom.TagName.DIV, {'class': 'items-container'});
      for (const env of study.getEnvironmentSpecsList()) {
        const envName = dom.createDom(
            dom.TagName.A, {'class': 'item', 'title': 'Record an episode'},
            env.getName());
        events.listen(envName, events.EventType.CLICK, e => {
          this.setPageStudy_(id, env.getId());
          e.preventDefault();
        });
        setHref(envName, getEnvUri(id, env.getId()));
        dom.appendChild(envsContainer, envName);
      }
      dom.append(
          row,
          createNonNumericCell(studyName),
          createNonNumericCell(study.getCreationTime().toDate().toUTCString()),
          createNonNumericCell(enabled),
          createNonNumericCell(study.getDescription()),
          createNonNumericCell(envsContainer),
          createNonNumericCell(edit),
      );
    }
    showElement('studies-container');
    hideElement('studies-intro');
  }

  /**
   * Refreshes the list of studies.
   * @private
   */
  refreshStudies_() {
    this.setBusy_();
    this.sendRequest(
        new OperationRequest().setSetStudies(new SetStudiesRequest()));
  }

  /**
   * Enables or disables the study.
   *
   * @param {!EnableStudyResponse} response Response for the enable study
   *     request.
   * @private
   */
  enableStudy_(response) {
    this.setBusy_(false);
    const enabled =
        /** @type {!MDLSwitchElement} */ (
            dom.getParentElement(
                getElement('enabled-' + response.getStudyId())))
            .MaterialSwitch;
    if (response.getEnabled()) {
      enabled.on();
    } else {
      enabled.off();
    }
  }

  /**
   * Update the current step.
   *
   * @param {!StepResponse} response Response for the step request.
   * @private
   */
  step_(response) {
    setTextContent('episode-index', response.getEpisodeIndex());
    setTextContent('episode-step', response.getEpisodeSteps());
    setTextContent('reward', response.getReward());
    displayImage(this.canvas_, response.getImage_asU8());
  }

  /**
   * Ask users for confirmation to save the terminated episode.
   *
   * @param {!ConfirmSaveResponse} response
   * @private
   */
  confirmSave_(response) {
    // Default response is to reject.
    this.saveDialog_.returnValue = 'reject';
    this.pressedKeys_.clear();
    checkCheckbox('save-mark-as-completed', response.getMarkAsCompleted());
    // This is non-blocking.
    this.saveDialog_.showModal();
  }

  /**
   * Handles gamepadconnected event.
   *
   * @param {!Event} e
   * @private
   */
  connectGamepad_(e) {
    const gamepad = /** @type {!GamepadEvent} */ (e).gamepad;
    this.showMessage_(`${gamepad.id} is connected.`);
    this.gamepadControllers_.set(gamepad.index, gamepad);
  }

  /**
   * Handles gamepaddisconnected event.
   *
   * @param {!Event} e
   * @private
   */
  disconnectGamepad_(e) {
    const gamepad = /** @type {!GamepadEvent} */ (e).gamepad;
    this.showMessage_(`${gamepad.id} is disconnected.`);
    this.gamepadControllers_.delete(gamepad.index);
  }

  /**
   * Updates the state of the gamepad controller inputs.
   * @private
   */
  updateGamepadInputs_() {
    let inputChanged = false;
    for (const gamepad of navigator.getGamepads()) {
      // First pad will always be null.
      if (!gamepad || !this.gamepadControllers_.has(gamepad.index)) {
        continue;
      }
      const prevGamepad = this.gamepadControllers_.get(gamepad.index);
      if (prevGamepad.timestamp == gamepad.timestamp) {
        // No change in the state of the gamepad.
        continue;
      }
      this.gamepadControllers_.set(gamepad.index, gamepad);
      inputChanged = true;
    }
    if (inputChanged) {
      this.sendKeys_();
    }
  }

  /**
   * Called to drive animation.
   * @private
   */
  runAnimation_() {
    this.updateGamepadInputs_();
    if (!this.isPaused_) {
      window.requestAnimationFrame(() => this.runAnimation_());
    }
  }

  /**
   * Sets the pause state of the environment.
   *
   * @param {!PauseResponse} response Pause response.
   * @private
   */
  pause_(response) {
    this.setBusy_(false);
    this.isPaused_ = response.getPaused();
    showElement('paused', this.isPaused_);
    if (!this.isPaused_) {
      this.runAnimation_();
    }
  }

  /**
   * Sets the camera.
   *
   * @param {!SetCameraResponse} response Response for the set camera request.
   * @private
   */
  setCamera_(response) {
    showElement('env-camera');
    let name = response.getName();
    if (!name) {
      // Use index as the name.
      name = response.getIndex();
    }
    setTextContent('env-camera-name', name);
  }

  /**
   * Shows or hides the study editor.
   *
   * @param {boolean=} show Whether to show or hide the editor.
   * @private
   */
  showStudyEditor_(show = true) {
    showElement('edit-study-tab', show);
    switchToTab(show ? 'edit-study-tab' : 'studies-tab');
  }

  /**
   * Handles the response received from the client.
   *
   * @param {!OperationResponse} response Response for a request.
   * @protected
   */
  handleResponse(response) {
    switch (response.getTypeCase()) {
      case OperationResponse.TypeCase.CONFIG:
        const studyEditor = new StudyEditor(
            'edit-study-', JSON.parse(response.getConfig().getConfig()));
        this.studyEditor_ = studyEditor;
        events.listen(
            studyEditor, events.EventType.RESET,
            e => this.showStudyEditor_(false));
        events.listen(studyEditor, events.EventType.SUBMIT, e => {
          const study = studyEditor.getStudy();
          this.setBusy_();
          this.sendRequest(new OperationRequest().setSaveStudy(
              new SaveStudyRequest().setStudy(study)));
          // Study editor will be closed when the response is received.
          e.preventDefault();
        });
        this.hasConfig_ = true;
        this.maybeSetPage_();
        break;
      case OperationResponse.TypeCase.SET_STUDIES:
        this.setStudies_(
            /** @type {!SetStudiesResponse} */ (response.getSetStudies()));
        this.hasStudies_ = true;
        this.maybeSetPage_();
        break;
      case OperationResponse.TypeCase.SELECT_STUDY:
        this.setStudy_(
            /** @type {!SelectStudyResponse} */ (response.getSelectStudy()));
        break;
      case OperationResponse.TypeCase.SELECT_ENVIRONMENT:
        this.setEnvironment_(/** @type {!SelectEnvironmentResponse} */ (
            response.getSelectEnvironment()));
        break;
      case OperationResponse.TypeCase.CONFIRM_SAVE:
        this.confirmSave_(
            /** @type {!ConfirmSaveResponse} */ (response.getConfirmSave()));
        break;
      case OperationResponse.TypeCase.SAVE_EPISODE: {
        const episode =
            /** @type {!SaveEpisodeResponse} */ (response.getSaveEpisode())
                .getEpisode();
        if (episode) {
          showElement('episodes-container');
          this.addEpisode_(episode, 0);
        }
        break;
      }
      case OperationResponse.TypeCase.EPISODES:
        this.setEpisodes_(
            /** @type {!EpisodesResponse} */ (response.getEpisodes()));
        break;
      case OperationResponse.TypeCase.DELETE_EPISODE:
        this.deleteEpisode_(
            /** @type {!DeleteEpisodeResponse} */ (
                response.getDeleteEpisode()));
        break;
      case OperationResponse.TypeCase.REPLAY_EPISODE:
        this.setReplayEpisode_(
            /** @type {!ReplayEpisodeResponse} */ (
                response.getReplayEpisode()));
        break;
      case OperationResponse.TypeCase.REPLAY_STEP:
        this.replayStep_(
            /** @type {!ReplayStepResponse} */ (response.getReplayStep()));
        break;
      case OperationResponse.TypeCase.ADD_EPISODE_TAG:
        this.addEpisodeTag_(
            /** @type {!AddEpisodeTagResponse} */ (
                response.getAddEpisodeTag()));
        break;
      case OperationResponse.TypeCase.REMOVE_EPISODE_TAG:
        this.removeEpisodeTag_(/** @type {!RemoveEpisodeTagResponse} */ (
            response.getRemoveEpisodeTag()));
        break;
      case OperationResponse.TypeCase.ADD_STEP_TAG:
        this.addStepTag_(
            /** @type {!AddStepTagResponse} */ (response.getAddStepTag()));
        break;
      case OperationResponse.TypeCase.REMOVE_STEP_TAG:
        this.removeStepTag_(
            /** @type {!RemoveStepTagResponse} */ (
                response.getRemoveStepTag()));
        break;
      case OperationResponse.TypeCase.UPDATE_REPLAY_EPISODE:
        if (!/** @type {!UpdateReplayEpisodeResponse} */ (
                 response.getUpdateReplayEpisode())
                 .getSuccess()) {
          this.showError('Unable to save the episode.');
        }
        break;
      case OperationResponse.TypeCase.DOWNLOAD_EPISODES:
        this.setDownloadProgress_(/** @type {!DownloadEpisodesResponse} */ (
            response.getDownloadEpisodes()));
        break;
      case OperationResponse.TypeCase.SAVE_STUDY:
        // Response is not used.
        this.showStudyEditor_(false);
        this.refreshStudies_();
        break;
      case OperationResponse.TypeCase.ENABLE_STUDY:
        this.enableStudy_(
            /** @type {!EnableStudyResponse} */ (response.getEnableStudy()));
        break;
      case OperationResponse.TypeCase.ERROR:
        this.showError(response.getError().getMesg());
        break;
      case OperationResponse.TypeCase.PAUSE:
        this.pause_(/** @type {!PauseResponse} */ (response.getPause()));
        break;
      case OperationResponse.TypeCase.STEP:
        this.step_(/** @type {!StepResponse} */ (response.getStep()));
        break;
      case OperationResponse.TypeCase.SET_CAMERA:
        this.setCamera_(
            /** @type {!SetCameraResponse} */ (response.getSetCamera()));
        break;
    }
  }

  /**
   * Initializes DOM object global variables and clears input boxes. This must
   * be called from onload handler of body element.
   */
  constructor() {
    /**
     * Environment that is being played.
     * @private @type {?EnvironmentSpec}
     */
    this.currentEnv_ = null;
    /**
     * Episode that is being replayed.
     * @private @type {?Episode}
     */
    this.currentReplay_ = null;
    /**
     * Current step of the episode that is being replayed.
     * @private @type {number}
     */
    this.currentReplayIndex_ = -1;
    /**
     * ID of the environment to load after the study is set.
     * @private @type {?string}
     */
    this.envToLoad_ = null;
    /**
     * Chip elements keyed by their labels for the tags of the episode being
     * replayed.
     * @private @type {!Object<string, !Element>}
     */
    this.episodeTagChips_ = {};
    /**
     * Chip elements keyed by their labels for the tags of the current step of
     * the episode being replayed.
     * @private @type {!Object<string, !Element>}
     */
    this.stepTagChips_ = {};
    /**
     * Step tag annotations.
     * @private @const @type {!Map}
     */
    this.stepTagAnnotations_ = new Map();
    /** @private @const @type {!Map} */
    this.gamepadControllers_ = new Map();
    /** @private @const @type {!Html5History} */
    this.history_ = new Html5History();
    /** @private @type {boolean} */
    this.hasConfig_ = false;
    /** @private @type {boolean} */
    this.hasStudies_ = false;
    /** @private @type {boolean} */
    this.isInitialized_ = false;
    /** @private @type {boolean} */
    this.isPaused_ = true;
    /** @private @const @type {!Set<string>} */
    this.pressedKeys_ = new Set();
    /** @private @type {?StudyEditor} */
    this.studyEditor_ = null;

    // These containers and elements are initially hidden.
    ['env-container', 'episodes-container', 'replay-container',
     'studies-container', 'edit-study-tab', 'env-camera', 'episodes-loading']
        .forEach(hideElement);

    /** @private @const @type {!Element} */
    this.snackBar_ = /** @type {!Element} */ (dom.getElement('snackbar'));

    /** @private @const @type {!HTMLTableElement} */
    this.episodesTbl_ =
        /** @type {!HTMLTableElement} */ (dom.getElement('episodes-tbl'));
    const tableSorter = new TableSorter();
    tableSorter.setDefaultSortFunction(TableSorter.alphaSort);
    // Steps and total reward are numeric columns.
    tableSorter.setSortFunction(7, TableSorter.numericSort);
    tableSorter.setSortFunction(8, TableSorter.numericSort);
    tableSorter.decorate(this.episodesTbl_);

    /** @private @const @type {!HTMLTableElement} */
    this.studiesTbl_ =
        /** @type {!HTMLTableElement} */ (dom.getElement('studies-tbl'));

    const canvas = /** @type {!HTMLCanvasElement} */ (dom.getElement('canvas'));
    /** @private @const @type {!HTMLCanvasElement} */
    this.canvas_ = canvas;
    canvas.addEventListener('keydown', e => this.handleKeyDown_(e));
    canvas.addEventListener('keyup', e => this.handleKeyUp_(e));

    const selectStudy = new Select('Select...');
    /** @private @const @type {!Select} */
    this.selectStudy_ = selectStudy;
    selectStudy.setId('study');
    selectStudy.setEnabled(false);
    selectStudy.render(dom.getElement('study-label'));

    const selectEnv = new Select('Select...');
    /** @private @const @type {!Select} */
    this.selectEnv_ = selectEnv;
    selectEnv.setId('environment');
    selectEnv.setEnabled(false);
    selectEnv.render(dom.getElement('environment-label'));

    events.listen(
        selectStudy, EventType.ACTION,
        e => this.requestSelectStudy_(
            /** @type {string} */ (selectStudy.getValue())));
    events.listen(
        this.selectEnv_, EventType.ACTION,
        e => this.requestSelectEnvironment_(
            /** @type {string} */ (selectEnv.getValue())));

    const selectQuality = createSelect('quality', 'quality-label', [
      {'id': Quality.QUALITY_LOW, 'label': 'Low'},
      {'id': Quality.QUALITY_MEDIUM, 'label': 'Medium'},
      {'id': Quality.QUALITY_HIGH, 'label': 'High'},
    ]);
    events.listen(selectQuality, EventType.ACTION, e => {
      const quality =
          /** @type {!SetQualityRequest.Quality} */ (selectQuality.getValue());
      this.sendRequest(new OperationRequest().setSetQuality(
          new SetQualityRequest().setQuality(quality)));
    });

    const saveDialog =
        /** @type {!HTMLDialogElement} */ (dom.getElement('save-dialog'));
    /** @private @const @type {!HTMLDialogElement} */
    this.saveDialog_ = saveDialog;
    // We listen to the close event and send the response to handle cases in
    // which the user doesn't click one of the buttons in the dialog, e.g.
    // presses the escape key.
    events.listen(saveDialog, EventType.CLOSE, e => {
      const markAsCompleted = isChecked('save-mark-as-completed');
      this.sendRequest(new OperationRequest().setSaveEpisode(
          new SaveEpisodeRequest()
              .setAccept(saveDialog.returnValue == 'accept')
              .setMarkAsCompleted(markAsCompleted)));
      canvas.focus();
    });
    events.listen(
        dom.getElement('save-accept'), events.EventType.CLICK, function(e) {
          saveDialog.close('accept');
        });
    events.listen(
        dom.getElement('save-reject'), events.EventType.CLICK, function(e) {
          saveDialog.close('reject');
        });

    const downloadDialog =
        /** @type {!HTMLDialogElement} */ (dom.getElement('download-dialog'));
    /** @private @const @type {!HTMLDialogElement} */
    this.downloadDialog_ = downloadDialog;
    events.listen(
        dom.getElement('download-close'), events.EventType.CLICK, function(e) {
          downloadDialog.close();
        });
    events.listen(
        getElement('download-copy-to-clipboard'), events.EventType.CLICK,
        function(e) {
          // Clear the selection.
          const selection = window.getSelection();
          selection.removeAllRanges();
          const range = document.createRange();
          // Select the URL.
          range.selectNodeContents(dom.getElement('download-link'));
          selection.addRange(range);
          // Copy to the clipboard and clear the selection.
          document.execCommand('copy');
          selection.removeAllRanges();
        });
    /** @private @const @type {!MDLProgressElement} */
    this.downloadProgress_ =
        /** @type {!MDLProgressElement} */ (
            dom.getElement('download-progress'));

    // Frames/sec slider.
    const fps = dom.getElement('fps-slider');
    events.listen(fps, EventType.CHANGE, e => {
      const value = e.target.value;
      this.sendRequest(
          new OperationRequest().setSetFps(new SetFpsRequest().setFps(value)));
      setTextContent('fps', value);
      canvas.focus();
    });

    events.listen(
        dom.getElement('env-fullscreen'), events.EventType.CLICK, e => {
          dom.getElement('env-canvas').requestFullscreen().catch(err => {
            const message = /** @type {!TypeError} */ (err).message;
            this.showError(`Unable to enable full-screen mode: ${message}`);
          });
          canvas.focus();
        });

    /** @private @const @type {!HTMLCanvasElement} */
    this.replayCanvas_ =
        /** @type {!HTMLCanvasElement} */ (dom.getElement('replay-canvas'));
    this.replayCanvas_.addEventListener(
        'keydown', e => this.handleReplayKeyDown_(e));

    /** @private @const @type {!MDLSliderElement} */
    this.replayStepSlider_ =
        /** @type {!MDLSliderElement} */ (dom.getElement('replay-step-slider'));
    events.listen(
        this.replayStepSlider_, EventType.CHANGE,
        e => this.requestReplayStep_(parseInt(e.target.value, 10)));

    /** @private @const @type {!google.visualization.LineChart} */
    this.replayRewardChart_ = new google.visualization.LineChart(
        /** @type {!Element} */ (dom.getElement('replay-reward-chart')));
    google.visualization.events.addListener(
        this.replayRewardChart_, events.EventType.SELECT, () => {
          const selection = this.replayRewardChart_.getSelection();
          for (const item of selection) {
            this.requestReplayStep_(item['row']);
          }
        });
    /** @private @type {?google.visualization.DataTable} */
    this.replayRewardData_ = null;

    events.listen(
        dom.getElement('replay-add-episode-tag'), events.EventType.CHANGE,
        e => this.handleAddEpisodeTag_(e));
    events.listen(
        dom.getElement('replay-add-step-tag'), events.EventType.CHANGE,
        e => this.handleAddStepTag_(e));
    events.listen(
        dom.getElement('replay-episode-save'), events.EventType.CLICK,
        e => this.handleUpdateEpisode_());

    events.listen(
        dom.getElement('download'), events.EventType.CLICK,
        e => this.handleDownloadEpisodes_());

    events.listen(dom.getElement('status-valid'), EventType.CHANGE, e => {
      const show = this.canShowInvalidEpisodes_();
      const rows = dom.getElementsByTagNameAndClass(
          dom.TagName.TR, 'invalid', this.episodesTbl_);
      for (let i = 0, n = rows.length; i < n; ++i) {
        style.setElementShown(rows[i], show);
      }
      e.preventDefault();
    });

    events.listen(
        dom.getElement('studies-tab'), events.EventType.CLICK,
        e => this.refreshStudies_());

    events.listen(dom.getElement('new-study'), events.EventType.CLICK, e => {
      this.studyEditor_.reset();
      this.showStudyEditor_();
    });

    // Listen gamepad (dis)connected events. These are not available under
    // closure.
    window.addEventListener('gamepadconnected', e => this.connectGamepad_(e));
    window.addEventListener(
        'gamepaddisconnected', e => this.disconnectGamepad_(e));
  }

  /**
   * Sets the page to that of a study.
   *
   * @param {string|undefined} id ID of the study.
   * @param {string=} envId ID of the environment. If specified, then the
   *     environment will be set to this one after the study is loaded.
   * @private
   */
  setPageStudy_(id, envId) {
    if (id === undefined) {
      this.showError('Invalid study.');
      return;
    }
    if (envId) {
      this.envToLoad_ = envId;
    }
    this.requestSelectStudy_(id);
  }

  /**
   * Sets the page based on the URL fragment.
   * @private
   */
  setPage_() {
    const fragment = new Uri(window.location).getFragment();
    if (!fragment) {
      return;
    }
    const uri = new Uri(fragment);
    switch (uri.getPath()) {
      case 'replay': {
        const studyId = uri.getParameterValue('study');
        const sessionId = uri.getParameterValue('session');
        const episodeId = uri.getParameterValue('episode');
        if (studyId === undefined || sessionId === undefined ||
            episodeId === undefined) {
          this.showError('Invalid episode to replay.');
        } else {
          this.requestReplayEpisode_(studyId, sessionId, episodeId);
        }
        break;
      }
      case 'study':
        this.setPageStudy_(uri.getParameterValue('id'));
        break;
      case 'env':
        // We first need to load the study and then the environment.
        this.setPageStudy_(
            uri.getParameterValue('study'), uri.getParameterValue('id'));
        break;
    }
  }

  /**
   * Sets the page if the initialization steps have completed.
   * @private
   */
  maybeSetPage_() {
    if (this.isInitialized_ || !this.hasConfig_ || !this.hasStudies_) {
      return;
    }
    this.isInitialized_ = true;
    this.setPage_();
  }
}

exports = {App};
