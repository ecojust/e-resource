# 泗泾路28号住宅东端双层砖券窗与凹槽壁柱

Antigng 于 2017 年 8 月 31 日从街对面拍摄了泗泾路 28 号。照片右侧的红砖壁柱和两层窗券都能在同一张原片中辨认。上海市第五批优秀历史建筑名录将此处列为 5A016，现用途为住宅，历史名称一栏列有长丰木行、协隆申庄、永隆号、大中织造厂。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [署名原照](https://commons.wikimedia.org/wiki/File:%E6%B3%97%E6%B3%BE%E8%B7%AF28%E5%8F%B7.jpg) · [实际模型](../../../sijing-28-brick-arched-window-bay.html)

每层的券砖呈放射状砌筑，红灰砖组交替排列，向下可见拱底。浅色券石的位置、券砖之间的放射缝和红砖薄边按原片分段测量。红砖壁柱有上下两处凹槽，内砌蓝灰砖，下层另有一处小孔。整排墙体留出两处窗洞。上层有两扇白色外开窗，下层三扇木窗分别有两道横梃。窗后淡色帘布的纹理以简化的竖褶表达。[券面与拱底的逐砖测线](measurements/arch-outlines.json) · [五扇窗的铰边与开角](measurements/casement-trace.json) · [砖缝间距](measurements/wall-courses.json)

采用 2.65 米名义窗宽及上下窗台间 3.24 米名义高差建立坐标。两层窗扇开角、壁柱进深、檐带挑出量和帘布后的空间深度属于单张照片的估计。砖色取样、玻璃和木框反映拍照当时的外观。原图中的临时晾衣、电线和空调遮住了部分构件，砖缝在短段遮挡处按相邻纹路延续。28 号与 30 号的门牌点同在既有建筑轮廓内，故这段窗间立面在独立页面展示。[摄影参数](measurements/photographic-reference.json) · [位置复核](measurements/footprint-review.json)

三个导出网格各通过 111 条射线，覆盖券面、窗框、五片外开窗、壁柱凹槽和小孔。其中 19 条穿过前两版模型的窗洞边缘与外券座浆处，修订后均命中窗洞内的实体。另取原照的 135 个独立位置，三个网格都命中了对应的红灰砌面或浅色券石。[原照与三档砖材的首交复核](measurements/released-window-arch-review.json)

## 从源码重建

在本项目完整工作树中，从此目录运行以下命令。最后两行从原始照片重新计算券面和墙面灰缝。

```sh
python source/build_model.py --output sijing-full.glb
python source/build_model.py --lod --output sijing-low.glb
python source/build_blender_source.py --check-raw sijing-full.glb
python measurements/trace-faces.py original-photo.jpg rebuilt-arches.json
python measurements/measure-brick-intervals.py original-photo.jpg rebuilt-courses.json
```

[逐砖券面](source/measured_arches.py) · [两层外开木窗](source/casements.py) · [墙身与壁柱](source/east_wall.py) · [七个镜位](source/cameras.json) · [来源与许可](SOURCES-LICENSE.md)
