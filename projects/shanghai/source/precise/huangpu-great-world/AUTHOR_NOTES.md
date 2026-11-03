# 大世界模型制作说明

本次新建 `huangpu-great-world` 的几何，按修缮后可见外观制作黄浦区西藏南路 1 号大世界沿街 U 形四层主楼、街角多级塔和两座可见屋顶亭。全局入口为 `index.html#landmark=huangpu-great-world&mode=overview`；`great-world.html` 是辅助模型检查页。

## 依据与边界

实际看过 2014 年俯照、2024 年 Commons 01–05 夜间街景，以及 TimeOut 2017 年场地页日光照片。来源与逐图记录由相邻 `source-register.json`、`photo-review.json`、`documentary-review.json` 保留。日光图用来近似浅米墙与浅灰石柱/栏杆色，夜景照用于结构、窗格、装饰与可读“大世界”字牌；照片灯光色没有直接作为日光材质。2017 场地页的实际拍摄日期没有署明。

2014 照片中的白色钢结构中庭罩是复开前证据，当前屋盖未得到明确照片核对，因此本轮不建。没有据此宣称现状屋盖已拆除，也没有把院内演艺空间或室内做成已完成部分。共舞台 source2367 独立保留。

地图主轮廓来自 source1519（w369238007@12），塔位置由完全重叠的 source497（w1197556192@1）与外观照片共同定位；OSM 六顶点不是六柱证据。主楼贴共舞台一边向内让 0.15 m，外挑檐带也扣除邻体缓冲区。模型没有铺整院地坪。Author ENU 为东/北/上，GLB 为东/上/南，heading 0，锚点见参数文件。

## 原创构造与估计项

主楼采用一个连续周界壳，窗洞是实际空洞，窗玻璃与棕色网格退进墙内。本栋 helper 的玻璃背板覆盖完整洞口并向墙内搭接 12 mm，修补独立射线发现的窗周圈细缝，前表面仍退进 0.32 m；旧建筑的 helper 未改。普通街翼的花瓶石栏与入口菱形/圆形镂空石栏分开制作；柱头卷涡、窗楣和壁柱为简化原创几何，不宣称逐片雕刻复原。店招、广告、临时灯串和无可靠字样的刻字未添加。

主塔底层按地图街角关系定位，屋面第一圈按照片制作 12 个拱开间，以上两层直柱廊保留退后的窗芯体。柱间有真实空隙；每段顶部有连续天花/顶板，与下部芯体及上层平台厚度搭接。两座屋顶亭也保留外柱、退后芯体、连续层盖和浅穹顶。塔尖近似浅灰米色，亭盖单独用较深灰色，均非实测色。

主屋面 20.4 m、尖顶 43.8 m、细杆顶 46.4 m 是照片比例估计，文献未核出明确实测塔高；不要采用源地图推定 30 m 作为竣工测量。亭位置、大小、隐蔽侧窗节奏、开口深度、层高、字形和细部尺寸也是估计。两处“大世界”字牌按 2024 图中较大的字牌近似为约 3 m 字高，用自行绘制的笔画几何，不含字体文件或照片贴图。

普通主屋面的灰色面退至墙内并低于石墙盖 0.04 m，二者在厚度方向搭接，没有同高灰面/石盖叠片。塔和亭的屋面内盖也低于周圈檐盖并向外搭接。真实导出三角的屋面覆盖检查独立于构造组件闭合检查，避免“组件各自封闭但整栋接缝漏空”。

## 可移植重建

`source/` 含原创布局、参数和工具。Python 依赖在 `requirements.txt`；GLB 为自包含几何，无外链纹理。通用闭合体/窗洞导出、序列化检查、native 保存重开与打包框架复用了上一栋的 MIT helper，逐项来源与 SHA256 见 `HELPER_PROVENANCE.json`，没有复用上一栋建筑网格。原始和 LOD 从同一构造独立生成，LOD 减少柱/栏/拱的细分，保留 U 形、真实窗洞和开敞塔亭。

在本目录运行：

```sh
python -m pip install -r source/requirements.txt
mkdir -p build
python -B source/build_model.py --out build/huangpu-great-world-raw.glb
python -B source/build_model.py --lod --out build/huangpu-great-world-lod-uncompressed.glb
python -B source/verify_author.py --out build/author-raw.json
python -B source/verify_roof_coverage.py --asset build/huangpu-great-world-raw.glb --out build/roof-coverage.json
blender --background --factory-startup --threads 4 --python source/build_native.py -- --raw build/huangpu-great-world-raw.glb --out build/huangpu-great-world.blend --previews build/native --samples 16
python -B source/package_assets.py --raw build/huangpu-great-world-raw.glb --lod build/huangpu-great-world-lod-uncompressed.glb --native build/huangpu-great-world.blend --out build/packaged --gltfpack /path/to/gltfpack
```

交付使用 gltfpack v0.25 的 `-cc -noq -vnf -km -kn -ke`，保留 FLOAT32 顶点、不做量化减面。`decode_meshopt.mjs` 接受显式的外部 Meshopt decoder 路径，用于解码后逐材质、有向三角摘要与 raw/LOD 比对。

Blender 文件包含可编辑网格、材料和单独的预览布景集合。地面、光源、相机仅属于预览布景，没有进入 GLB。原生预览来自同一份 raw；保存后实际重开 `.blend`，核对模型三角数和几何 hash。`native.json` 如实记录先渲染后保存重开的顺序。

## 许可与验证

原创模型与代码采用 MIT；OpenStreetMap 参考轮廓遵循 ODbL-1.0。第三方原图未嵌入或随模型发布，各自许可见来源登记。新交付审计仅含本栋作者检查、序列化/屋面检查、原生预览和重建/绑定记录；邻体/地图/浏览器核对另由本栋集成审计记录。
