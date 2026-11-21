# 徐家汇观象台1908年钟塔与两翼

从南面的双向石阶登上平台，入口券门的放射状石块和上方砖檐分成两层。两翼在中段退后，前伸的翼楼上留有两列券窗和红砖饰板。钟室之上是带半圆山花的方塔和封闭测风室。这个模型取自1908年出版图中的形制。

[旋转查看馆舍](../../../zikawei-observatory-1908.html) · [同馆垂直气压计](../../../zikawei-museum-french-vertical-barometer.html) · [1908年版面](https://commons.wikimedia.org/wiki/File:Tcitp_d391_the_observatory_at_siccawei.jpg)

## 年代与形制

上海市优秀历史建筑第四批名录将蒲西路166号列为4D047。现存馆舍建于1901年。1908年出版的《Twentieth Century Impressions of Hong-kong, Shanghai, and other Treaty Ports of China》清楚画出钟室上方的砖木房间、拱窗、平台栏杆和顶部小罩。约1925年观象台自己的刊物中，同一位置已是开敞金属架。两种形制可对读。[上海市房管局登记](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [1908年原书](https://archive.org/details/twentiethcentury00wriguoft) · [约1925年馆方出版图](https://commons.wikimedia.org/wiki/File:L%27Observatoire_de_Zi-Ka-Wei.jpg)

1920年《Zi-Ka-Wei》平面图逐段标出两翼、夹部和中心塔的进退。两幅独立屋面影像给出的现存馆舍全长约49米，估计误差约2米。历史简图东端另有一段小凸部；1908年照片所见东翼末端外透出天空，因此本模型的主体收在两翼之间，长约46.4米。《气象知识》的博物馆参观记述记下原门厅罗盘所示的朝南格局。[1920年平面](https://commons.wikimedia.org/wiki/File:Plan_de_Zi-Ka-Wei_%28Shanghai-XuJiaHui%29.jpg) · [尺寸与分段读数](measurements/estimated-building-dimensions.json) · [博物馆参观记述](http://www.qxkp.net/tjzx/202606/t20260625_7880742.html)

## 对照照片制作

在800像素宽的1908年版面上，先取东西两翼和入口的窗台、券顶及檐口，再用钟室与高室可见的侧面、东翼边缘校准拍摄角度。按此相机重新投影三维模型，入口、左右窗列及塔身的参考点加权误差约2.8像素。单独留出的西翼第二窗列四点误差约2至2.5像素。模型中最高杆端约38米，钟室钟面中心约18米，属于照片估算。靠后的窗扇、顶部仪器的精确形制和钟面时间仍有不确定性。[点位与透视误差](measurements/1908-corner-constrained-camera.json) · [1908年原图与模型同角度对照](study-views/1908-book-and-model.jpg) · [模型投影](study-views/1908-model-projection.jpg) · [首版与后续校正记录](../../../data/audit/zikawei-observatory-1908-v1/preflight/revisions)

砖纹为原创，灰砖墙使用重复纹理，红砖券和券缝、窗框、钟面刻度、石阶栏杆以及两层塔身间的承托都建成实物网格。建筑现貌和2025年影像帮助辨认砖色与工艺。[当代材料对照](https://www.news.cn/local/20251227/101441bd999647cd89320184e3f397d2/c.html) · [来源与使用条件](SOURCES-LICENSE.md)

## 重建

安装项目的建筑建模依赖后，可从本目录导出原始近景、远景或整套资产。整套资产另需要 Blender、gltfpack 和 Open Image Denoise。

```sh
python source/build_model.py --output observatory-full.glb
python source/build_model.py --output observatory-lod.glb --lod
python source/build_model.py --out export --audit audit
```

[两翼与钟塔](study-views/whole-front.jpg) · [钟面](study-views/clock-face.jpg) · [入口石阶](study-views/stair-portal.jpg)
