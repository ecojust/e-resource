# 外滩18号：v4.4 连续墙芯修复

这次只修复石块之间意外贯穿墙厚的空缝。保留 v4.3 的建筑比例、全部原始网格、窗洞、材质和照片 UV；不宣称所有细网格线消失，石材分块的边界继续保留。

## 修复依据与范围

旧 `wall_rect(..., masonry=True)` 用 0.54 m 厚的独立石块，横向缩 0.012 m、竖向缩 0.014 m，却没有背衬，形成贯穿整个墙厚的空隙。斜看时这些空隙露出暗处，成为明显黑线。

本版只增加主立面和退台前墙两片连续墙芯，沿原来 30 个窗、门和柱廊洞口留空。墙芯前面退入石面 **18 mm**，背面到 525 mm，避免与原石块 540 mm 背面重合。**18 mm 退距、浅灰颜色及构造解释都是建模估计，不是现场测量。**

新墙芯使用每片墙统一的 X/Z 网格；正背面共享节点，只有墙体与洞口的边界生成侧面，不在相邻实墙单元之间生成内部面。原始 128,046 个有向三角及其坐标、法线、UV 等属性在最终原始 GLB 中逐条完全相同；仅增加 2,328 个三角。30 个洞口定义保持一致，150 个洞内采样点均未被填堵。

同机位纯 Three.js 对比已确认贯通黑洞得到填补；这是保留石材分缝的结构修复。整合地图后的浏览器验收另行进行。

## 独立基线与一键重建

本包包含独立的 `baseline/bund18-v4.3.blend`，来自 Git 提交 **13fa900f8559b1c38154178d3af54e4d0591a5d3**，不是运行时将被覆盖的 `assets/native/bund/bund18.blend`。

- 仓库：[ecojust/e-resource](https://github.com/ecojust/e-resource)
- [冻结原生文件](https://raw.githubusercontent.com/ecojust/e-resource/13fa900f8559b1c38154178d3af54e4d0591a5d3/projects/shanghai/assets/native/bund/bund18.blend)
- 原生 SHA-256：`d1c7f62aecc10720ad2c7355df8372000b9127fa079dd080183005fbacc633e5`
- 从原生文件导出的旧版 GLB SHA-256：`803b987addf24d6a2eb788c9014770e9fdcd11506a1255f1302bb1ccd34dfd35`

此包及其基线即可离线重建，不需要下载旧模型，也不读取项目当前模型。使用 **Blender 4.3.2（glTF exporter 4.3.47）**、**gltfpack 1.3**、Python 3 和 NumPy：

```sh
python source/bund/chartered_bank/photo-v4.4/rebuild_all.py --output exported/bund18-v4.4 --project .
```

若工具不在 PATH，增加 `--blender /path/to/blender --gltfpack /path/to/gltfpack`。`--project` 提供项目内 Three.js/meshopt 解码器以执行额外的压缩几何检查；源码包移出项目后可省略，结构、照片和来源检查仍执行。

流程先从冻结原生文件重导出旧 GLB 并验证其完整 SHA，再加墙芯、验证全部原始三角/材质不变，最后生成网页和 LOD。输出 `bund18-photo.glb`、`bund18-photo-web.glb`、`bund18-photo-lod.glb`、`bund18-photo.blend` 以及 `asset-files.json`、`asset-metadata.json` 和验证报告。中间文件保留在输出的 `work/` 下。`.blend` 保存路径等元数据可能使其字节 SHA 因重建目录不同而变化；GLB 的逐字节可重建结果及几何检查另行记录。

`baseline/build_geometry-v4.3.py` 是冻结的开孔定义依据，只用于核对本次墙芯参数；实际重建从随包原生基线开始。`baseline/provenance.json`、`wall-core-input.json` 保留版本和校验和。

## 压缩和许可

网页模型使用 `-cc -noq -km -ke`。LOD 另加 `-si 0.35 -se 0.002 -sp`；目标比例不等于实际减面结果。**原始、网页、LOD 三套都保留同一张照片**，不生成新的贴图，也不剥除 LOD 的照片。

照片作者 **ScareCriterion12**，2021 年外滩麦加利银行照片，[原图页面](https://commons.wikimedia.org/wiki/File:%E4%B8%8A%E6%B5%B7%E5%A4%96%E6%BB%A9%E9%BA%A6%E5%8A%A0%E5%88%A9%E9%93%B6%E8%A1%8C%E6%97%A7%E5%9D%802021.jpg)，许可 **[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)**。照片纹理模型与随包原生基线继续按 CC BY-SA 4.0 发布；原创代码适用项目 MIT；地图轮廓保留 © OpenStreetMap contributors、ODbL 1.0 署名。

三套 GLB 嵌入的 JPEG 均为原始 **798,956 B**，SHA-256 `26a1219fe534659ae78bae9dfc498aef30b50b957172046a5c401906758315ba`。原生文件内亦打包此图。`compress_models.py` 会恢复 gltfpack 丢弃的 `asset.copyright`，保留作者、照片来源和许可链接。照片像素不改变，v4.3 的局部照片映射范围也不改变。
