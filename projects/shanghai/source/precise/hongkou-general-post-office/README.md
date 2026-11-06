# 上海邮政总局历史主楼与钟塔

[全局主图](../../../index.html#landmark=hongkou-general-post-office&mode=overview) · [辅助近远景与下载](../../../postal-office.html) · [四资产清单](../../../assets/models/candidates/hongkou-general-post-office/manifest.json) · [本轮验收](../../../data/audit/postal-office-v1/README.md)

本件按修缮后可见照片制作地图主源 1959 范围内的有界外观：南、东两侧三层高巨柱和青绿窗间板，第四层退入开廊，北侧红砖立面，东南单钟面的圆鼓肩钟楼、八柱透空上亭及曲线铜绿冠顶。两组各三人的铜像以原创简化坐姿／倚姿轮廓表示，钟面、石瓮、窗框、字牌和檐口有实际立体几何；没有复制第三方模型或使用照片纹理。

中庭罩采用 **2010 年实见照片中的弧形网格形态**，主楼内界、罩宽与分格为作者估计，不能解释为 2026 年现场测量或当前维护状况已经核清。西侧相接源 3148 保留，照片左端的相邻筒拱建筑不自动并入本件。院底只有有界平面，没有展厅陈设、完整室内或室内漫游。

## 尺寸与范围

- 采用上海地方志《上海名建筑志》记述的名义总高 **49.5 米**，另加 **8.2 米旗杆**；模型最高点为约 57.7 米。百科的 **51.16 米**异文继续保留。四层主体 19.5 米、钟楼段顶 32.5 米、上亭檐口附近 42 米等为本模型分段估计，不能当成逐层实测。
- 官方正文北苏州路 **276 号**与 2019 年保护牌照片的 **250 号**分别保留；主楼身份以文字、照片与源对象综合确认。历史初建、后续修缮、现存复制铜像不是同一年代原物。
- 原地图只有整块外框，没有真实内院或墙线分段。U 形内界、层高、柱距、隐面与屋顶小体均由资料约束后估计，未用总建筑面积或展区面积强行缩放足迹。
- 外墙相对地图作者包络内退约 0.85 米，为街墙前巨柱保留真实空间；低矮 U 形基座沿有界合同，西侧公共边保守退让。显示裁剪与结构碰撞另按实际三种几何检查，院内铺地不得当成建筑墙体碰撞。
- 屋面仅表达照片可见的有限围护、两个低矮服务小体和两处低矮种植体；具体位置、内院完整立面、设备和其余建筑群仍未全面复原。

[逐文核对](documentary-review.json) · [逐图核对](photo-review.json) · [来源登记](source-register.json) · [资料口径](REFERENCE_NOTES.md) · [地图合同](footprint-contract.json) · [建模参数](source/model-parameters.json)

## 文件与重建

四类资产的精确字节数、三角面数及 SHA256 以 manifest 为准。原始 GLB 和 Blender 保留近景细节；网页 GLB 使用 Meshoptimizer 无坐标量化压缩；LOD 减少柱面、铜像、栏杆及微小砖缝的细分，保留单钟、通亭、字牌、主立面与弧罩。

源码在 `source/`，普通几何依赖见 `source/requirements.txt`。从仓库根目录使用独立输出目录运行，路径按本机环境设置：

```sh
POSTAL_SOURCE=projects/shanghai/source/precise/hongkou-general-post-office/source
POSTAL_OUTPUT=/absolute/scratch/postal-model
python -m pip install -r "$POSTAL_SOURCE/requirements.txt"
python "$POSTAL_SOURCE/build_model.py" --out "$POSTAL_OUTPUT/raw.glb"
python "$POSTAL_SOURCE/build_model.py" --lod --out "$POSTAL_OUTPUT/lod.glb"
blender -b --threads 4 --python "$POSTAL_SOURCE/build_native.py" -- --raw "$POSTAL_OUTPUT/raw.glb" --out "$POSTAL_OUTPUT/postal.blend" --previews "$POSTAL_OUTPUT/previews" --samples 16
python "$POSTAL_SOURCE/package_assets.py" --raw "$POSTAL_OUTPUT/raw.glb" --lod "$POSTAL_OUTPUT/lod.glb" --native "$POSTAL_OUTPUT/postal.blend" --out "$POSTAL_OUTPUT/assets" --gltfpack /absolute/path/to/gltfpack
```

原生预览的地面、相机和灯光放在独立展示集合，不属于建筑资产。保存后脚本实际重开 `.blend` 并比对建筑几何；它不会把未重新渲染的旧图称为重开后的新截图。具体使用版本与通过范围以本轮验收记录为准。

本轮保留侧鼓暗面板修正前的八个视角及其原始哈希；修正后另渲染完整正面和左右侧鼓三个视角，并重开最终 Blender 文件。逐面差集证明仅两个暗面板的 24 个三角面变化，旧八图只用于其余未变部分，详见本轮 `side-panel-revision-equivalence.json` 和两阶段 `native.json`。

## 许可与精度

原创建模代码和几何按 [MIT](LICENSE)；地图参考保留 © OpenStreetMap contributors／ODbL-1.0。第三方照片和网页只作研究，没有随模型嵌入或公开再分发。

“人民邮电”“上海邮政博物馆”采用 **Noto Serif CJK SC** 的许可字形子集，更名为 Postal Sign Subset；字体软件单独采用 **SIL OFL 1.1**，见 [字体说明及完整许可](source/common/fonts/README.md) 和 [字体来源](source/font-subset-provenance.json)。字形宽高、位置与笔意是估计，没有声称描摹原招牌。上述 MIT 不覆盖附带字体软件或 OSM 派生数据。

这是照片与公开资料约束下的外观模型，不是测绘、摄影测量或完整历史原貌复原。[作者说明](AUTHOR_NOTES.md) 记录构造选择和已知限制。
