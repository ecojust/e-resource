# 逐栋照片参照建筑：共享生成工具

普通Python环境需要 `numpy`、`shapely>=2.1`、`Pillow`、`fonttools`；相机校准和采样控制再生另需 `scipy`；原生工程步骤使用Blender 4.3或更新版本。几何生成使用米制east/north/up坐标，GLB导出为east/up/-north。不要在Blender的独立Python环境里直接运行依赖Shapely的建模步骤。

在相邻 `bundNN` 目录运行该栋的 `build_model.py`，具体校准、照片选择和验证入口见各自README。公共几何工具使用带真实开口的连续墙体；玻璃、框、装饰及字牌为独立实体。照片映射只作用于明确选中的玻璃，原JPEG字节嵌入GLB。窗户逐口校准，不能将全立面一个投影当作每块凸窗或凹玻璃的正确位置。

```sh
python common/test_photo_architecture.py
python common/test_photo_metric.py
python common/test_photo_extensions.py --photo bund05/research/nissin-2025-suicasmo-original.jpg
blender -b --python common/blender_finish.py -- \
  --glb bundNN/output/bundNN.glb --output /path/to/native --render
python common/package_building.py --id bundNN --raw bundNN/output/bundNN.glb \
  --native /path/to/native/bundNN.blend --project /path/to/shanghai \
  --gltfpack /path/to/gltfpack --output /path/to/new-package --lod-without-photos
```

`package_building.py`只写新的独立目录，不注册导航，不覆盖现有模型。它保留原始GLB和Blender字节，为网页制作Meshopt压缩版本，并验证远景轮廓极值变化不超过0.35米。不含照片的几何远景仍是简化模型；轮廓极值检查不是完整形状误差或外观准确性证明。`--lod-without-photos`仅在远景将照片玻璃换为说明过的近似色玻璃，以减少解码内存；原始、近景和原生工程保留照片。

字牌用 `fonts/BundSignSubset.otf` 的许可字形生成实体，保留OFL许可和源字体记录。字形可读但不是品牌字体描摹；仅字形接触节点使用0.5毫米轮廓公差与0.05毫米节点量化，使薄字在Float32下仍为闭合实体。

高度和开间以已记录来源及照片比例为依据，未见侧后、墙厚、雕饰和部分深度仍有推定，不是测绘成果。数学、几何、JPEG字节、浏览器方向和实景对照是不同检查，各自的报告说明其范围。

原始代码和程序几何采用项目MIT许可；源轮廓保留OpenStreetMap/Overture ODbL署名，照片按各栋列出的原始许可分发。新模型均须单文件小于100 MB，按栋打包，不依赖Git LFS。
