# 哥伦比亚乡村俱乐部主楼

按 2018 年修缮设计图与多视角照片复原的外部建筑模型，包含保留的东加建、北侧门廊和圆端楼梯、南侧长廊与露台。现代店名按照片采用「蔦屋書店 / TSUTAYA BOOKS」。不包含独立游泳池、健身房、海军俱乐部或整个上生·新所园区。

这不是测绘模型。地图原始四边形只用于确定建筑归属、锚点和大致轴线；实际墙线按带 5 m 图尺的平面图推估，没有把所有凸出部位强塞入地图四边形。首层、二层、主檐、主脊和最高烟囱分别采用约 0.75、5.4、9、12、14 m 的图纸推定值，至少保留约 ±0.5–1 m 的尺度不确定性。两个剖面分别标定，未混用像素比例。详见 `drawing-calibration.json` 和 `DRAWING_CALIBRATION.md`。源数据的 22.1 m 粗尺度高度未采用。

模型包括真实墙洞、分级木窗格和扇光、北窗凹拱、钻石透孔、南面三格一组的细花格、成对柱及叶饰涡卷柱头、扭柱、开放铁艺阳台、玻璃护栏、分体坡屋顶及实体筒瓦、曲面楼梯塔帽、台阶与图纸所示弧形通路。内侧只建楼板、局部结构墙和入口楼梯，不推造不可见家具和装修。玻璃与窗框仍在洞中，因此“墙洞”不代表用户能穿过关着的窗。

南侧山花处于上层露台后墙，沿原主厅中轴，而非含东加建后的全楼中轴；与长廊前栏约相隔 6.3 m。东翼加建的墙色、金属窗和屋面与原西翼区分。北门廊八柱依平面布为四角成对；东西侧低扁拱有照片支持，正北外洞数仍为图纸推定。历史鹰饰缺少可靠图像，未重建。

`build_model.py` 保留通过体量核对的低量级阶段；`build_detailed.py` 是完整模型入口；`club_roof.py` 建立西班牙式筒瓦屋面。LOD 单独编写，减少瓦密度、曲面分段、柱头细饰和路面分缝，保留建筑开口及主要轮廓，不是把整体模型自动压成盒子。

## 原始材质与参考照片

完整 GLB 嵌入三张未经像素编辑的 ambientCG Plaster001 原始 JPEG：颜色、OpenGL normal、灰度粗糙度。历史与加建抹灰使用约 1.15 m 的平铺尺度，normal 强度为 1.6；LOD 仅嵌入同一张原始颜色图。它们是 **CC0 通用抹灰材质，不是本楼实测或实拍表面扫描**，颜色调节仅在 PBR 参数中进行。屋瓦、门窗、石材与雕饰为作者几何和参数材质。原图 SHA、贴图槽及使用范围在两份 texture whitelist 中逐项记录。

公开照片来自 WQL 的 2018 年 Wikimedia Commons 图片，采用 CC BY-SA 4.0，作为建筑形态参考；这些照片没有映射进模型。现代招牌与建筑师图纸另有私有研究参考，仅在说明中记述观察结果和来源，不随模型分发原图片。`public-photo-register.json` 的第一项始终是真实建筑照片，通用材质另标识 `generic_material_scan`。

招牌文字使用 Noto Sans CJK JP 的少量字形子集（SIL OFL 1.1），字形可辨但不是对商业标志字体的精确复制。南字牌相对主门宽度按同平面照片比例约 1.4 倍推估，不宣称实测。

## 生成与验证

Python 3、numpy、Shapely 2.1+、fontTools；Blender 4.3；gltfpack 1.3。所有输出必须使用新的目录，不覆盖已有阶段。

```sh
python build_detailed.py --out /path/to/new-full
python build_detailed.py --lod --out /path/to/new-lod
blender -b -t 2 --python render_previews.py -- --glb /path/to/new-full/columbia-country-club.glb --out /path/to/new-preview --samples 32
python verify_features.py /path/to/new-full/columbia-country-club.glb /path/to/new-full/feature-probes-input.json /path/to/new-full/feature-probes.actual.json
```

预览地面、灯光和摄像机放在独立集合；原始 GLB 与 native 建筑集合只有模型本体。124 条有限射线检查实际 GLB 中墙洞和邻接实体，以及花格孔和实角。这是局部建筑几何验证，不表示 HTML 漫游引擎已实现楼梯或三角网格碰撞。网页导航与视角由集成阶段独立核验。

完整和 LOD 分别压缩，保留原始位置、UV、法线精度及原图字节；使用 `-cc -noq -vtf -vnf -km -ke`，再由网页同源 Three/Meshopt 解码器比较真实三角面和 UV。单文件硬限制为 100,000,000 字节；原始 GLB 与 native 目标均低于 40 MB。
