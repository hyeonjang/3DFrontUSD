# Scene synthesis dataset fileformat converter

Scene synthesis datasets, [3d-future](https://tianchi.aliyun.com/specials/promotion/alibaba-3d-future) and [3d-front](https://tianchi.aliyun.com/specials/promotion/alibaba-3d-scene-dataset) are currently using their own format that is not compatible for the general computer graphics application.
This code coverts the trainning specific dataset to the general scene description format [Universal Scene Description](https://openusd.org/release/index.html).

## Description

To convert the 

## Getting Started

### Dependencies

We provide the dockerfile to set up the USD environment.
[OpenUSD](https://github.com/PixarAnimationStudios/OpenUSD), [USD-Plugins](https://github.com/adobe/USD-Fileformat-plugins).

```cmd
docker build -t YOURIMAGE .
```

Or directly configure your environment. Under Python version 3.10, and USD version 23.11
```cmd
apt-get update && apt-get install -y --no-install-recommends \
	git \
	build-essential \
	cmake \
	nasm \
	libxrandr-dev \
	libxcursor-dev \
	libxinerama-dev \
	libxi-dev && \
	rm -rf /var/lib/apt/lists/*

pip3 install -U Jinja2 argparse pillow numpy && \
git clone --branch "v23.11" --depth 1 https://github.com/PixarAnimationStudios/USD.git usd && \
python3 usd/build_scripts/build_usd.py usd/build/ --no-examples --no-tutorials --no-imaging --no-usdview --no-materialx --no-draco --build-variant release

export PATH="usd/build/bin:$PATH"
export LD_LIBRARY_PATH="usd/build/lib:$LD_LIBRARY_PATH"
export PYTHONPATH="usd/build/lib/python:$PYTHONPATH"

apt-get update && apt-get install -y libopencv-dev openimageio-tools libopenimageio-dev python3-openimageio && \
    git clone https://github.com/adobe/USD-Fileformat-plugins && \
    cmake -S ./USD-Fileformat-plugins -B ./USD-Fileformat-plugins/build -DCMAKE_INSTALL_PREFIX=bin -DUSD_FILEFORMATS_ENABLE_CXX11_ABI=ON -Dpxr_ROOT=./usd/build -DUSD_FILEFORMATS_ENABLE_FBX=false -DUSD_FILEFORMATS_ENABLE_GLTF=false -DUSD_FILEFORMATS_ENABLE_PLY=false && \ 
    cmake --build   ./USD-Fileformat-plugins/build --config release && \
    cmake --install ./USD-Fileformat-plugins/build --config release

export PATH="$PATH:./USD-Fileformat-plugins/bin/bin:./USD-Fileformat-plugins/bin/plugin/usd"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:./USD-Fileformat-plugins/bin/lib:./USD-Fileformat-plugins/bin/lib64"
export PXR_PLUGINPATH_NAME="$PXR_PLUGINPATH_NAME:./USD-Fileformat-plugins/bin/plugin/usd"
```

We only provide following format conversion, when we build USD-plugins.

- [x] OBJ
- [ ] PLY
- [ ] FBX
- [ ] GLTF

### Installing

If you want to build your own environment, please refer to the original repositories of [OpenUSD](https://github.com/PixarAnimationStudios/OpenUSD) and[USD-Plugins](https://github.com/adobe/USD-Fileformat-plugins).

### Executing program

`YOUR_FOLDER` should be same for the both commands.
To convert dataset files, use the following commands:

* Furniture convertor
```
python future_to_usd.py -i 3D_FUTURE_DATASET_PATH -o YOUR_FOLDER
```
* Front convertor
```
python front_to_usd.py -i 3D_FRONT_DATASET_PATH -o YOUR_FOLDER
```

#### Front including features
- [x] Object positions
- [x] Object metadata
- [x] Room Meshes
- [ ] Lights
- [ ] Materials

#### 3D Front USD plugins

Current included metadata.
- [ ] super-category
- [ ] category
- [ ] style
- [ ] theme
- [ ] material

## Authors

If you have any issue for this repo, please feel free to contact Hyeonjang An at <ahj1218@kisti.re.kr>.

## Version History

* 0.1
    * Initial Release

## License
