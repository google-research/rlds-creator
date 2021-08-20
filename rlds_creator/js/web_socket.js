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
goog.module('rlds_creator');

const OperationResponse = goog.require('proto.rlds_creator.client.OperationResponse');
const events = goog.require('goog.events');
const {App} = goog.require('rlds_creator.app');

class AppImpl extends App {
  sendRequest(request) {
    // We use the binary wire-format.
    this.socket_.send(request.serializeBinary());
  }

  isConnected() {
    // See https://developer.mozilla.org/en-US/docs/Web/API/WebSocket#constants.
    return this.socket_.readyState == 1;
  }

  constructor() {
    super();

    // Open the socket connection.
    const protocol = location.protocol == 'https:' ? 'wss://' : 'ws://';
    const socket =
        new WebSocket(protocol + location.host + '/channel/environment');
    // Change binary type from "blob" to "arraybuffer". Deserialization on the
    // server side requires the latter.
    socket.binaryType = 'arraybuffer';
    /** @private @const @type {!WebSocket} */
    this.socket_ = socket;

    socket.addEventListener(events.EventType.MESSAGE, e => {
      const response = OperationResponse.deserializeBinary(
          /** @type {!MessageEvent} */ (e).data);
      this.handleResponse(response);
    });

    socket.addEventListener(events.EventType.ERROR, e => {
      // Channel errors are not recoverable.
      this.showError('Session error. Please refresh the page.');
    });

    events.listen(window, events.EventType.UNLOAD, e => {
      // Close the socket on unload.
      socket.close();
    });
  }
}

goog.exportSymbol('rlds_creator.App', AppImpl);
