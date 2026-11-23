# 颐庆里住宅

景星路310弄的双柱弄门，与314弄题图中的砖砌街面，出现在Fayhoo于2015年4月6日先后拍摄的两幅照片里。两幅照片间隔五分多钟。模型根据窗台、窗头、山花、柱脚和屋盖的位置，将这两处放回同一条街的观察方向。[打开模型](../../../yiqingli-jingxing-310-314-lane-houses.html) · [原照与市级登记](measurements/registered-houses-and-photographs.json)

市级登记号为5G014。314弄街面模型宽约14.9米。310弄双柱之间可看见成对的山花，两者离街的距离采用独立街站交会估计。院内列屋的后缘依据四期航片概括，后部斜边的不确定性约为两至三米。十一处观察机位可分别检查街面细节和两排屋盖。[地理位置及边界](measurements/placement-identity.json) · [街面测量](measurements/streetside-triangulation.json) · [屋面与街线图](measurements/roof-and-street-footprints.svg)

## 复建

从上海项目根目录运行下列命令。所需工具包括Python与项目原几何依赖、Blender、Node.js和gltfpack。五幅原创程序纹理随源提供。运行包内的压缩步骤会逐面比对独立解码结果与作者网格。原生步骤重建编辑组，保存Blender工程并在另一个进程中重开，核对几何、纹理坐标、内嵌图像和机位。

```bash
S=source/precise/yangpu-yiqingli-jingxing-310-314-lane-houses/source
python "$S/build_model.py" --output exports/full-source.glb
python "$S/build_model.py" --lod --output exports/lod-source.glb
python "$S/package_model.py" exports packaged
python "$S/package_editable.py" prepare packaged native
python "$S/package_editable.py" run packaged native
```

网页的原始、近景和远景GLB分别取自`packaged`。Blender工程与四种下载文件的最终清单`four-role-manifest.json`位于`native`。成品清单内列有各文件的字节数和SHA-256。[来源与许可](SOURCES-LICENSE.md)
