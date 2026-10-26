# 逐栋精细建筑替换

新增楼使用独立覆盖文件接入原全市近景；原来的1,708个分块与169,320个近景文件保持原字节。运行时清单是 `data/precise-buildings-v6.json`，独立模型在 `assets/city-overrides-v6/`。

本批映射为日清大楼（bund05，local ID 810）、中国通商银行旧址（bund06，1293）和交通银行旧址（bund14，1700），共同位于宏分块 `14-13720-6694`。真实轮廓、OSM历史版本和Overture对象关系见 `source/bund/photo-rebuild-v6/bundNN/geometry-input.json`。

两个覆盖文件保留原文件全部202,428个展开三角形，把三个目标和14个邻居分成独立完整节点组。实际解码核验表明位置、材质归属和绕序守恒；Float32位置与法线一致。逐目标细模实际加载可见后，才隐藏对应普通楼；邻楼继续按正常近景距离加载。细模失败或退出时恢复相应普通楼表示，避免按半径删除或隐藏整个邻居文件。

可从完整项目的冻结源数据重新生成：

```sh
python build_precise_overrides.py --project /path/to/shanghai \
  --output /path/to/new-output \
  --geometry-input-root /path/to/shanghai/source/bund/photo-rebuild-v6 \
  --gltfpack /path/to/gltfpack
node verify_override_geometry.mjs /path/to/new-output/geometry-comparison-input.json
node verify_override_runtime.mjs /path/to/shanghai /path/to/new-output/precise-buildings-v6.json
```

依赖已发布的城市生成器、原宏分块 feature-table/READY/near 文件及 gltfpack。每个owner独立压缩，再合并buffer与节点，不能对合并结果再次整体运行gltfpack，否则实例可能移出所属节点。原始和解压后文件均须小于100,000,000字节；SHA和几何核验在清单及 `data/audit/precise-buildings-v6/`。

这些检查证明替换和邻楼保留正确；各栋外观的照片核验另见建筑源码包，不能用三角形一致性代替外观准确性。
