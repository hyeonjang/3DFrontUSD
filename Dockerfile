# Base Docker Image with Compiled Pixar USD Toolchain

# This Docker image serves as a base with a precompiled version
# of the Pixar USD toolchain. It is a separate image because
# USD tools take a significant amount of time to build and
# are not updated frequently. PLATTAR uses this base for various
# open-source projects, including the xrutils toolchain.

# For more information on USD tools, visit https://github.com/PixarAnimationStudios/USD
FROM python:3.10-slim-bookworm

# our binary versions where applicable
ENV WORK_DIR="/usd/"
WORKDIR WORK_DIR

ENV USD_VERSION="23.11"

# Update the environment path for Pixar USD
ENV USD_BUILD_PATH="${WORK_DIR}/usd"
ENV USD_PLUGIN_PATH="${USD_BUILD_PATH}/plugin/usd"
ENV USD_BIN_PATH="${USD_BUILD_PATH}/bin"
ENV USD_LIB_PATH="${USD_BUILD_PATH}/lib"
ENV PATH="${PATH}:${USD_BIN_PATH}"
ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${USD_LIB_PATH}"
ENV PYTHONPATH="${PYTHONPATH}:${USD_LIB_PATH}/python"


# Required for compiling the USD source
RUN apt-get update && apt-get install -y --no-install-recommends \
	git \
	build-essential \
	cmake \
	nasm \
	libxrandr-dev \
	libxcursor-dev \
	libxinerama-dev \
	libxi-dev && \
	rm -rf /var/lib/apt/lists/* && \
	# this is needed for generating usdGenSchema
	pip3 install -U Jinja2 argparse pillow numpy && \
	# Clone, setup and compile the Pixar USD Converter. This is required
	# for converting GLTF2->USDZ
	# More info @ https://github.com/PixarAnimationStudios/USD
	mkdir -p xrutils && \
	git clone --branch "v${USD_VERSION}" --depth 1 https://github.com/PixarAnimationStudios/USD.git usd && \
    python3 usd/build_scripts/build_usd.py ${USD_BUILD_PATH} --no-examples --no-tutorials --no-imaging --no-usdview --no-materialx --no-draco --build-variant release

# build adobe usd-plugins
RUN apt-get update && apt-get install -y libopencv-dev openimageio-tools libopenimageio-dev python3-openimageio && \
    git clone https://github.com/adobe/USD-Fileformat-plugins && \
    cmake -S ./USD-Fileformat-plugins -B ./USD-Fileformat-plugins/build -DCMAKE_INSTALL_PREFIX=bin -DUSD_FILEFORMATS_ENABLE_CXX11_ABI=ON -Dpxr_ROOT=${USD_BUILD_PATH} -DUSD_FILEFORMATS_ENABLE_FBX=false -DUSD_FILEFORMATS_ENABLE_GLTF=false -DUSD_FILEFORMATS_ENABLE_PLY=false && \ 
    cmake --build   ./USD-Fileformat-plugins/build --config release && \
    cmake --install ./USD-Fileformat-plugins/build --config release

ENV PATH="$PATH:${WORK_DIR}/USD-Fileformat-plugins/bin/bin:${WORK_DIR}/USD-Fileformat-plugins/bin/plugin/usd"
ENV LD_LIBRARY_PATH="$LD_LIBRARY_PATH:${WORK_DIR}/USD-Fileformat-plugins/bin/lib:./USD-Fileformat-plugins/bin/lib64"
ENV PXR_PLUGINPATH_NAME="$PXR_PLUGINPATH_NAME:${WORK_DIR}/USD-Fileformat-plugins/bin/plugin/usd"