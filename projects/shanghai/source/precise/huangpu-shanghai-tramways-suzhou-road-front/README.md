# 英商上海电车公司大楼临河立面与柱廊入口

南苏州路185号的临河立面有四条通高壁柱。每根柱顶下方各悬一个红色叶环，窗上有向外张开的五片窗楣。位于中央上层的阳台向街面挑出，弧形铁栏随台口转折。街层入口处，原照左边能区分两根相邻圆柱，右边另见一根。柱头带卷涡，上方横梁的区框与两端赤色托座在原照中清晰可辨。石券从门前的券面一直延伸到内退的门膛。[署名街照与原始参数](measurements/photographic-reference.json)

模型包括照片中的主街面、底层分缝、四道壁柱、窗框和门廊、两排长檐、曲面阳台与照片右端的一小段侧墙。以现存城市资料的18.631米街面作为名义尺度，按原照校正窗洞、花环轮廓、门券和柱身。檐口出挑、室内门扇位置、柱后回墙以及阳台栏杆深度采用摄影估计。街边车辆遮住了柱脚和底墙，临时电线、设备、广告和行人妨碍了若干部位的辨读。建筑邻近四川中路与虎丘路，测绘资料尚未将每个窗间定位至可靠的城市坐标。[窗洞与原照像素](measurements/facade-apertures.json) · [四圈叶环测量](measurements/four-photographed-wreaths.json) · [三柱券门](measurements/entrance.json) · [位置资料](measurements/footprint-review.json)

三个交付网格各测了四排窗洞、出挑线脚和入口侧壁。从2015年照片另取 82 个叶环与石柱位置，分别为 46 处红色叶面、20 处环心和 16 处外侧石柱；三个网格的材质首交均吻合。[从原照复核各处表面](measurements/released-wreath-review.json)

## 从源码重建

在本项目完整工作树中，从本目录运行以下命令。照片测量命令中的原片可从署名来源取得，需保留原始EXIF方向。

```sh
python source/paint.py
python source/build_model.py --output tramways-full.glb
python source/build_model.py --lod --output tramways-low.glb
python source/build_blender_source.py --check-raw tramways-full.glb
python measurements/record-facade.py
python measurements/trace-relief.py original-photo.jpg rebuilt-wreaths.json
```

[立面与窗框](source/frontage.py) · [阳台与铁栏](source/balcony.py) · [入口圆柱和石券](source/doorway.py) · [四处叶环](source/measured_wreaths.py) · [七个摄影机位](source/cameras.json) · [来源与许可](SOURCES-LICENSE.md)
