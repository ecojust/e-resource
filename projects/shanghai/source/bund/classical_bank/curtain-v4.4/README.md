# 外滩15号：v4.4 窗帘体修复（C）

本包接续[结构墙阶段](../wall-v4.4/README.md)，修正十个窗帘体的反向绕序，同时删除 120 个内部穿插褶皱盒。**纠正 425 个原生面 / 580 个三角的朝向，删除 720 个原生面 / 1,440 个内部穿插三角。** 它们不是零面积退化三角，不能与其他模型的零面积清理混同。

保留的全部顶点坐标不变，墙、96 个洞口、拱曲线、中央退进、柱、青铜窗框、题字及其余材质几何不变。原始和网页模型为 **92,848** 三角；LOD 为 **44,726** 三角，减面过程另行记录。

## 为什么采用 C

十个不透明窗帘体（5 矩形、5 拱形）的前面法线原本朝内，有向体积为负，朝向修正有独立几何证据。120 个褶皱盒位于不透明窗帘前面之后 10 mm，与窗帘体穿插，后端又伸出 5 mm。

root 在同机位纯 Three.js 中实测：

- A（只删除内部褶皱盒）：竖短杂纹消失。
- B（只修正十个窗帘体朝向）：杂纹仍存在，**B 作为杂纹修复方案被拒绝**。
- C（朝向修正 + 删除穿插盒）：杂纹消失，窗框与洞口完整，已接受。

所以不能把“修正法线”单独宣称为黑纹消除原因。原始 A/B/C 截图、哈希与结论保存在 `references/` 和 `ab-evidence.json`，未进行图片修饰。没有新增窗帘造型。

## 完整两阶段来源链

1. 原始模型 → 墙阶段：仅结构墙合并。旧保留报告的输入/输出哈希保留在 `baseline/upstream-wall-*.json`；94,288 / 46,138 三角和那些旧哈希只描述墙阶段。
2. 墙阶段 → 本窗帘阶段：反转十个窗帘体，并删除穿插褶皱盒。单独记录 580 个朝向修正三角与 1,440 个删除三角，不将最终哈希冒充墙阶段输出，也不宣称所有原三角仍被保留。

`asset-metadata.json` 与 raw metadata 建议完整保留 `wall_topology_cleanup`，另加 `curtain_repair` 明确本阶段例外。剩余位置不变与非窗帘有向三角属性完全一致，见 `curtain-native-validation.json`、`curtain-preservation.json`。

## 离线重建

独立冻结基线随包保存，不读取运行时将被覆盖的模型：

| 基线 | SHA-256 |
|---|---|
| `baseline/bund15-wall.glb` | `0b6ec1409ca5230da74b63b977a08420e493e75670fdb5047322d97ec001eb29` |
| `baseline/bund15-wall.blend` | `1ee61ebf1c5c525ded62efee045cd984c63e53ef4f7138a6c38be8e98d59c8d8` |

需要 Blender 4.3.2、gltfpack 1.3、Python 3 和 NumPy：

```sh
python source/bund/classical_bank/curtain-v4.4/rebuild_all.py --output exported/bund15-curtain-v4.4 --project .
```

工具不在 PATH 时增加 `--blender /path/to/blender --gltfpack /path/to/gltfpack`。完全不需要网络。`--project` 使用项目自带 Three.js/meshopt 解码器核对网页压缩模型；源码包移出项目可省略此附加检查。

输出 raw/web/LOD GLB、原生 `.blend`、asset-files、asset-metadata、raw metadata 建议及验证报告。`.blend` 保存路径等元数据可能导致其字节 SHA 随目录改变，三套 GLB 的字节可重建结果单独核查。

网页压缩为 `-cc -noq -km -ke`；LOD 另加 `-si 0.35 -se 0.002 -sp`。压缩后恢复 `asset.copyright` 和 `asset.extras`，同时保留墙阶段与窗帘阶段来源信息。

## 许可

全部模型均无图片纹理。Suicasmo 的 CC0 照片仍仅作建筑参照；既有原创模型/源码归属与 © OpenStreetMap contributors、ODbL 1.0 空间数据署名保持不变。未引入新的照片贴图或第三方模型。
