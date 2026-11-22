# 澳门路660弄27号山墙下的双门廊

绿底白字的「27」钉在右门旁。砖门框上方各有一扇灰石包边的半圆气窗，右门在照片中半开，可从侧面看到内退的门扇。楼上两扇格窗各带一处浅挑栏，下有三只托座。屋脊在檐口后方升起，一小片斜屋面削去了山墙尖顶。[打开模型](../../../aomen-660-no27-gabled-entrances.html) · [绿色门牌与门扇](study-views/passage.jpg) · [屋面与斜脊](study-views/hip.jpg)

## 哪一栋

第四批上海市优秀历史建筑 4N002 包含澳门路660弄的十一排住宅。27、29、31、33、35、37 号六个地址点沿同一栋建筑排列，两端相距约 27.0 米，依次沿东北至西南方向排列。这六个点都落在底图原建筑1475，41号位于另一栋。模型取27号照片内的双门廊和屋顶前段，保留整排底图。左邻门牌在图中辨不清。[市表原行](measurements/listed-site.json) · [六个门牌的平面示意](study-views/27-37-row.png) · [逐户坐标与建筑轮廓](measurements/address-row.json)

内外棉株式会社在20世纪20年代为管理人员修建这片花园里弄。区内有多种住宅式样，37号照片可见相似的门券，251号一带的庭院围墙和屋色已有明显区别。2018年的更新调查记录31幢住宅，其中11栋列为优秀历史建筑。[2018年上观报道](https://www.shobserver.cn/wx/detail.do?id=83601) · [2017年寻访](https://www.jfdaily.com/wx/detail.do?id=51374)

## 依据与尺度

中国の風景发表的现场照片可直接读出27号。行程页记为2015年3月12日，照片右下日期为3月13日。正面用于门窗位置，另一张斜视图用于辨认截头屋面。资料未给出现场实测尺度，以正面每像素约18毫米、门扇约1.7米高为估计；墙的厚度、门扇开角、栏杆进深和脊后短截面均为估计。墙面采用程序生成的黄赭色粗灰，门牌数字、屋面瓦片、扇窗、门扇和窗外栏杆均为几何。[逐图出处](measurements/photographic-sources.json) · [门券量测](measurements/paired-entries.json) · [来源和许可](SOURCES-LICENSE.md)

独立页面可切换近景和远景，下载原始 GLB、网页两档 GLB 及可编辑 Blender 工程。在仓库内运行下列命令复建。

```sh
python source/build_model.py --output aomen-27.glb
python source/build_model.py --lod --output aomen-27-lod.glb
python source/build_model.py --blender blender --out ./exports --audit ./audit
```
