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
We only provide following format conversion, when we build USD-plugins.

- [x] OBJ
- [ ] PLY
- [ ] FBX
- [ ] GLTF

### Installing

If you want to build your own environment, please refer to the original repositories of [OpenUSD](https://github.com/PixarAnimationStudios/OpenUSD) and[USD-Plugins](https://github.com/adobe/USD-Fileformat-plugins).

### Executing program

To convert dataset files, use the following commands:

* Furniture convertor
```
python future_to_usd.py DATAPATH
```
* Front convertor
```
python front_to_usd.py DATAPATH
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
