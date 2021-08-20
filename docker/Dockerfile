# Rendering in Mujoco fails with a shadow buffer error with the official Python
# image. We currently use the Tensorflow one instead.
# TODO(sertan): There may be a better option.
FROM ubuntu:20.04

# tzdata needs to be installed in non-interactive mode. Otherwise, it gets
# stuck asking for the time zone.
RUN apt-get update
RUN DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata

# Utilities.
RUN apt-get install -y curl gettext git python3-pip unrar unzip wget zip

RUN apt-get install -y --no-install-recommends \
    cmake \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    # mujoco_py dependencies.
    libgl1-mesa-dev \
    libglew-dev \
    libosmesa6-dev \
    patchelf

# Download and extract Mujoco.
RUN curl -k https://www.roboti.us/download/mjpro150_linux.zip --output /tmp/mujoco150.zip && \
    mkdir -p /root/.mujoco && \
    unzip /tmp/mujoco150.zip -d /root/.mujoco && \
    rm -f /tmp/mujoco150.zip
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/root/.mujoco/mjpro150/bin

# Robosuite uses Mujoco 2.0.
RUN curl -k https://www.roboti.us/download/mujoco200_linux.zip --output /tmp/mujoco200.zip && \
    unzip /tmp/mujoco200.zip -d /root/.mujoco && \
    mv /root/.mujoco/mujoco200_linux /root/.mujoco/mujoco200 && \
    rm -f /tmp/mujoco200.zip
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/root/.mujoco/mujoco200/bin

# Copy the Mujoco license key
COPY mjkey.txt /root/.mujoco/mjkey.txt

# The next step requires numpy being installed.
RUN pip3 install numpy
# mujoco_py dependencies.
RUN pip3 install \
    Cython \
    cffi \
    glfw \
    imageio \
    lockfile
# We install the mujoco_py package explicitly. gym and robosuite packages have
# conflicting requirements which cannot be resolved under Bazel.
RUN LD_LIBRARY_PATH=/root/.mujoco/mujoco200/bin pip3 install mujoco_py

# Install bazel. This is used to generate the Python protobuf libraries.
RUN echo "deb [arch=amd64] http://storage.googleapis.com/bazel-apt stable jdk1.8" | \
    tee /etc/apt/sources.list.d/bazel.list && \
    curl -k https://bazel.build/bazel-release.pub.gpg | \
    apt-key add - && \
    apt-get update && apt-get install -y bazel

# DMLab dependencies.
RUN apt-get install -y freeglut3 libffi-dev libsdl2-dev

# Build and install DeepMind Lab pip package.
# We explicitly set the Numpy path as shown here:
# https://github.com/deepmind/lab/blob/master/docs/users/build.md
RUN NP_INC="$(python3 -c 'import numpy as np; print(np.get_include()[5:])')" && \
    git clone https://github.com/deepmind/lab.git && \
    cd lab && \
    git checkout 2e4c62938a00bce6331a078558a8385438c17b51 && \
    sed -i 's@glob(\[@glob(["'"$NP_INC"'/\*\*/*.h", @g' bazel/python.BUILD && \
    sed -i 's@: \[@: ["'"$NP_INC"'", @g' bazel/python.BUILD && \
    sed -i 's@650250979303a649e21f87b5ccd02672af1ea6954b911342ea491f351ceb7122@1e9793e1c6ba66e7e0b6e5fe7fd0f9e935cc697854d5737adec54d93e5b3f730@g' WORKSPACE && \
    sed -i 's@rules_cc\/archive\/master.zip@rules_cc\/archive\/main.zip@g' WORKSPACE && \
    sed -i 's@rules_cc-master@rules_cc-main@g' WORKSPACE && \
    bazel build -c opt python/pip_package:build_pip_package --incompatible_remove_legacy_whole_archive=0 && \
    pip3 install wheel && \
    PYTHON_BIN_PATH="/usr/bin/python3" ./bazel-bin/python/pip_package/build_pip_package /tmp/dmlab_pkg && \
    ls /tmp/dmlab_pkg && \
    pip3 install /tmp/dmlab_pkg/deepmind_lab-*.whl --force-reinstall && \
    rm -rf /lab

# Install Atari ROMs.
RUN pip3 install atari-py
RUN mkdir roms && \
    cd roms && \
    wget http://www.atarimania.com/roms/Roms.rar && \
    unrar e Roms.rar && \
    unzip ROMS.zip && \
    unzip "HC ROMS.zip" && \
    rm ROMS.zip && \
    rm "HC ROMS.zip" && \
    rm Roms.rar && \
    python3 -m atari_py.import_roms .

# Robosuite dependencies.
RUN pip3 install h5py

# NetHack dependencies.
RUN apt-get install -y bison flex libbz2-dev

# Ensure that "python" command works.
RUN apt-get install -y python-is-python3

# For development purposes.
RUN apt-get install -y tmux vim

ADD . /rlds_creator/
WORKDIR /rlds_creator

# mujoco_py tries to resolve the path of the Mujoco key and library using the
# home directory of the user. This may be different from root, e.g. if running
# under GCP. We specify them explicitly.
ENV MUJOCO_PY_MJKEY_PATH=/root/.mujoco/mjkey.txt
ENV MUJOCO_PY_MUJOCO_PATH=/root/.mujoco/mujoco200
# dm-control adds a platform suffix.
RUN ln -s /root/.mujoco/mujoco200 /root/.mujoco/mujoco200_linux

# Build the Python binary. Some dependencies have assets with spaces in their
# paths. Bazel cannot handle them unless inprocess_symlink_creation option is
# enabled.
RUN bazel build --experimental_inprocess_symlink_creation rlds_creator:server

# Run the server.
CMD python3 bazel-bin/rlds_creator/server --port=$PORT
