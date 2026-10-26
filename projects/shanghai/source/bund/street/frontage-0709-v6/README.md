# 外滩 07／09 临街铺装：可离线重建的冻结源码

本归档以已发布 first3 街景为输入，追加 07／09 两处主临街缺失面：317.9617752㎡、100 个三角形。原 first3 的 844.5004115㎡、全部旧几何和障碍保留。铺装位置、宽度和高度是冻结道路与建筑边界之间的有界建模推定，不是测量成果。

`inputs/source-manifest.json` 锁定所有输入的大小和 SHA256。每个 `file` 都相对于本归档的 `inputs/`；其中绝对 `source` 字段仅记录来源，不参与读取。重建无需原 staging 目录、网络、Blender或下载旧城市模型。现有 `source/bund/street/frontage-v6/` 是前一批历史归档，不能删改。

先备好 `requirements.txt` 中的 Python 库及 gltfpack 1.3.0，版本与包文件哈希见 `dependencies.json`。依赖安装可能需要软件包源；下面的模型重建本身完全离线。不要用全新依赖版本替代锁定版本后声称逐字节重现。

在项目根目录运行，输出到全新目录；这个命令不会安装或改写现有模型：

```sh
PYTHONDONTWRITEBYTECODE=1 python tools/build_bund_street.py --gltfpack /path/to/gltfpack --output /tmp/bund-street-0709-rebuild
```

也可直接从本归档构建：

```sh
PYTHONDONTWRITEBYTECODE=1 python append_frontage.py --inputs inputs --output /tmp/bund-street-0709-direct --ids bund07 bund09 --gltfpack /path/to/gltfpack
PYTHONDONTWRITEBYTECODE=1 python test_frontage_bounds.py -v
```

验证入口会检查模型与支持面哈希一致、保留旧二进制前缀和所有旧 feature／障碍，以及仅新增两条支持面。`evidence/` 保存已完成的实际 Three/Meshopt 解码、运行时支持、重新构建与平面检查证据；它们不是一次新的网页或现场实测验收。

原始街道数据、足迹和冻结几何输入保留各自来源与许可元数据；不得将 Overture 数据统称为 OSM 实测。归档没有新增照片纹理。每个源文件和模型都小于 100,000,000 字节。

此源码归档不含第三方 Python/Node 运行库。程序与 gltfpack 的调用参数保持已验证版本；项目既有工具和原始依赖声明继续适用。
