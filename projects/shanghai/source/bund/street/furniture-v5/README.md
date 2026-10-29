# 外滩街景家具：可整合交付

这里是独立工作目录，未修改主项目或 Git。建模只改滨江灯、护栏、道路灯三类；未改建筑、道路范围、绿化或既有 OSM 岸线。

## 已完成

- 滨江灯：渐细杆身、下窄上宽灯笼、四根实体笼条、上下箍圈和浅圆顶。总高 4.53m 为照片比例估计。
- 护栏：8 根细圆横杆、粗圆扶手、倾斜支撑、底板及带盖石柱。顶高 1.16m、斜倾 0.28m、细杆半径 13mm 为照片比例估计。
- 道路灯：黑色渐细立杆、平滑上升曲臂、略向上倾的扁椭圆灯头及下部灯面；立杆保留伸到灯臂上方的形态。
- 原 24 盏滨江灯、8 盏路灯、95 根石柱的位置和估计间距保留；752 根护栏斜撑沿原岸线。照片不证明这一实例清单是现实精测清单。

形态参考 `furniture-evidence.json`。主要图片是 Bohao Zhao 2011 年 CC BY 3.0 原图与 Suicasmo 2025 年 CC0 原图；不是统一年代的现状测绘。照片未用作纹理。2011 照片可见垃圾桶，但无法可靠定位到当前模型区段，因此没有编造坐标。道路交通信号 OSM 节点未用来推断灯杆坐标。

## 整合方式

1. 将 `street_furniture.py` 放到主项目 `source/bund/street/`。
2. 将 `references/roadlamp-sassoon-2025-original.jpg`、`furniture-evidence.json` 放到相同相对位置。已有 `references/promenade-day.jpg` 不必复制。
3. `apply_furniture.py` 的 `apply(text)` 只替换旧 `lamp` 函数、原 `TRACK_RAIL=True` 的护栏生成段，并补充家具 metadata。可用于已合并铺装/绿化的新脚本；若相关锚点已改变会失败，需要按下列接口手动合并。
4. 原 `M`、`COLORS`、`face`、`rod`、`cuboid`、`Mesh` 定义后调用 `furniture=install_furniture(globals())`，令 `lamp=furniture.lamp`。在已计算 `rail`、`shore`、`waterward` 后调用 `post_count,lamps=furniture.build_railing(rail,shore,waterward,vector_at)`。
5. 保留原岸线顶点检验、道路/水域/建筑交集检验。将 `furniture.audit()` 保存至 metadata / `bund-streets-furniture-check.json`。
6. 压缩用 `gltfpack -cc -noq -kn -km -ke`。整段街道跨度很大，默认坐标量化会损伤 13mm 横杆；当前版本保留 float32 位置。

`audit().placements` 给出每个灯的 local X/Z 和概略包络；精确碰撞须读 `furniture-interaction.json`：所有家具实际发射调用同步收集 box、cylinder_segment、vertical_frustum、ellipsoid，包含立杆、方座、栏杆石柱、横杆和斜撑。两个灯座都是0.32m方形、y=.035→.255；并非仅有细杆圆心。栏杆沿既有 `railing_centerline`，顶高变为 1.16m；地图原点仍为 `(121.4862,31.2385)`，X东/Y上/Z南。

## 样本与验证

- `sample/source/bund/street/bund-streets.glb`：完整街景，仅替换家具后的样本，7.41 MB，137,794 三角。
- `bund-streets-furniture-web.glb`：压缩样本，2.44 MB；不是最终合并铺装/树木后的街景。
- `fitting-specimen.glb`：8m 护栏、滨江灯、道路灯独立实物样本，0.16 MB，2,716 三角。
- `fitting-specimen-render.png`：Blender 从上述真实 GLB 渲染的检视图，非生成式效果图；中性检视场景，不代表主项目光照。
- `fitting-specimen-check.json`：新增旋转体与椭球每个三角均朝外，无退化面。
- `furniture-decode-check.json`：使用项目实际 Three r180 GLTFLoader 和 MeshoptDecoder 解码。压缩前后 137,794 三角、零退化；68,690 个唯一位置逐点完全一致。
- 样本 `bund-streets-shoreline-check.json`：3009 岸线采样和 27,992 家具/石柱顶点通过；中心线距真实岸线最大 0.65m，顶点最大 0.967162m，未入水。
- 原道路、铺装、连接铺装和种植带检查仍全部通过。所有单文件低于 100 MB。

本交付没有运行浏览器，也没有改动主项目 runtime 或发布到 GitHub。`decode_furniture.mjs` 可用 Node 重跑实际解码检查；`build_fixture.py` 可重建独立样本，`render_fixture.py` 可用 Blender 重渲染。

代码和新建家具几何遵循原项目 MIT；OSM 派生布局保留 ODbL 归属，照片归属见证据清单。
