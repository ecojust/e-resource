# Bund05 · Nissin Building / 日清大楼 · 逐栋照片复原

以2025年Suicasmo CC0原图复原临江正面，以2011年Can Pac Swire CC BY-SA2.0东南斜视核对南立面。已按独立相机尺度复核修正主要正面比例，原玻璃深度版本已通过独立原生模型固定机位预览核对；网页场景验收由主项目继续完成。这仍是照片比例复原，不是实测建筑模型。具体原图、错图排除、年代冲突、可观测/推定对照见[研究记录](research/README.md)与`research/SOURCES.json`。

当前几何保留冻结OSM原16节点轮廓及临江20.142632898m边，增加四主开间、两组三面折线凸窗（各跨3层）、中部通高壁柱、双三角山花及弧顶阁楼窗、中央双小窗和石栏杆、下部双拱窗、两侧深入口及圆门柱、广东路侧小阳台和连续檐线。窗洞由墙面多边形差集真正开孔；有洞壁、内退玻璃和独立框。不是照片平板，也没有生成街灯、人车贴图。中央六组窗按实际行列分成112片凹入玻璃，逐片对应2025原图；全部玻璃合为一个照片材质，墙/框/石柱未贴图。

`calibration-independent.json`记录Canon官方传感器规格、24mm EXIF与原图控制点的透视核算；`calibration.json`据此选取主檐23.8m、山花28.9m、后部独立石fin29.4m，并缩小此前偏宽的窗。凸窗深度和细构件尺寸仍为照片比例估计。正面按可数的6层建立，OSM的7层标签不能直接强加为第七层完整正面。南侧连续四列与后端至少三列阳台、近角侧向阁楼浅拱和山花已用2011原图再核对；将照片轴分配至地图折线、远端间距与后部窗位仍属明确标注的推定。北侧前端保留实拍盲墙。底座按可见及遮挡推定的两组三孔做真实凹口；门头采用可读立体金字和近似菱形标志。

## 重建

源码安装布局为`source/bund/photo-rebuild-v6/{common,bund05,...}`。需要Python、numpy、Shapely2.1+、fontTools，不需要联网或Blender即可生成GLB。

```sh
python -B build_model.py --output /path/to/isolated-output
```

生成`bund05.glb`、逐构件`bund05.geometry.json`和`geometry-report.json`。单GLB严格小于100 MB。`check_geometry.py`在本包output重建并核对每个实际构件的闭合、绕序、正体积和FLOAT32数值；它不替代照片形状验收，也不证明不同装饰构件之间无有意相交。

Blender原生文件可由相邻公共`blender_finish.py`从原GLB导入生成。预览地面/相机归入独立Preview_only集合，不属于模型源。渲染由主任务统一调度，不在本脚本中自动执行。

## 许可与范围

原创几何和代码MIT；冻结地图轮廓与派生定位按ODbL-1.0署名OpenStreetMap/Overture。2025年Suicasmo CC0原图已按原字节嵌入玻璃材质；2011年Can Pac Swire CC BY-SA2.0原图仅供几何参照且独立保留该许可。不将代码MIT扩展到原照片。字体子集及OFL许可证位于相邻common/fonts。研究网页缓存无再分发许可声明，发布时只选原图、证据JSON和整理说明，不发布整个HTML缓存目录或错误建筑图片。

## 逐片玻璃核验

`photo-glass-controls.json`保存6组原始正向像素四角、窗格位置和112片采样区；`register_photo_glass.py`可用Pillow/SciPy重算JSON，生产重建不需要这两个分析依赖。`photo_glazing.py`只读这些控制点，把原始JPEG以bufferView嵌入，不重采样贴图。`research/glazing-controls-review.png`是带控制框的研究图，原JPEG文件保持不变，不能用此研究图作模型纹理。

`check_photo_uv.py --output /path/to/output`直接核验GLB原图SHA/字节、单照片材质、112片玻璃对应448个UV角、EXIF坐标回转和其他构件无照片材质。修订前版本已查看固定机位原生预览，主要正面轮廓、逐窗照片方向与窗格层次通过核对；网页近景/远景切换和实际灯光仍由主项目单独验收。数值及原生预览通过不等于实测精度。外侧折线凸窗、阁楼、下层门窗保留普通几何材质，不能将六组中央窗的映射描述成全立面照片复原。

## 玻璃嵌框修订

本轮只把同种窗构造的玻璃前移到现有窗框前脸后20mm，玻璃厚度仍20mm；这是明确的构造估计，不是实测退距。墙洞、窗框前后面和形状、照片、UV、锚点及三角形总数保持。细节和源SHA见[修订依据](glazing-depth-revision.json)，逐材质及玻璃实体差异见[几何比较](glazing-depth-difference.json)。旧源码快照与原生预览另存 [glazing-depth-history](glazing-depth-history/README.md)，附完整输入 SHA 校验和独立恢复命令，仅适用于旧模型。新候选已通过构建、闭合、原图与UV检查；原生预览已由root明确核对，浏览器复验仍单独进行。修订已同步到项目源码与模型；最终浏览器复验仍待完成。

## 修订资产与原生检查

原始、网页、Blender及无照片远景变体已独立打包。原始与原生副本保留原字节，网页经实际解码核对三角位置、法线与UV；原JPEG保留。当前文件大小如下（MB），每件均小于100 MB。

| 文件 | 大小（MB） | 下载 |
|---|---:|---|
| 原始GLB | 14.91 | [下载](../../../../assets/models/bund/bund05.glb) |
| 网页GLB | 8.73 | [下载](../../../../assets/models/bund/web/bund05.glb) |
| Blender工程 | 24.07 | [下载](../../../../assets/native/bund/bund05.blend) |
| 远景GLB（无照片） | 2.07 | [下载](../../../../assets/models/bund/lod-v4/bund05.glb) |

root已实际查看本修订的原生预览；照片和窗框的核对范围见[记录](native-preview-review.json)。浏览器同视角及场景复验另行完成，不以原生预览替代。完整封装、LOD与来源版权检查见[打包摘要](packaging-summary.json)。

[本修订原生预览](../../../../assets/previews/bund/bund05-v6.png)；[公开玻璃差异审计](../../../../data/audit/precise-buildings-v6/bund05/glass-depth-difference.json)。
