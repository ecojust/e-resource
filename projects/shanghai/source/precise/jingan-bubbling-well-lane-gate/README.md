# 涌泉坊愚园路中央拱门与门楼

上海市房屋管理局首批优秀历史建筑名录 1B003 登记「涌泉坊」，门牌为愚园路 395 弄 1–24 号。《静安区志》记载 1934 年动工、1936 年建成，杨润玉、杨元麟、周济之设计。入口位于愚园路南侧，正中过街楼与东西住宅合成近 50 米长、约 14 米高的沿街立面。本文只交付正中门楼。保护地块内的住宅、东西砖面突出部及其余入口仍须分别考证。[市房屋管理局首批名单](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [《静安区志》涌泉坊](https://web.archive.org/web/20160326135058/http://www.shtong.gov.cn/newsite/node2/node4/node2249/node4412/node17436/node18415/node18427/userobject1ai6785.html)

2007 年斜面实拍将中央门楼与两侧住宅分别定位。2009 年临街照显示中央大拱、一对小拱、石柱头、立面的栗褐色面砖、中层波浪形窗檐、上层拱窗扇光和中央扭纹石柱。白石匾上的字从右至左读「湧泉坊」。模型将三字轮廓从石匾稍微凸起。后侧墙和阁楼按可见轮廓估计，通道内的活动铁门扇收向两侧。真实管理时间及当下通行条件未作调查。[2009 年正面照](https://commons.wikimedia.org/wiki/File:Bubbling_well_lane.jpg) · [2007 年斜面照及 2014 年邻宅辨认](reference-review.json) · [《上海名建筑志》](https://web.archive.org/web/20180616182739/http://www.shtong.gov.cn/newsite/node2/node71994/node81772/node81776/node81788/userobject1ai109105.html)

19 级正射影像可辨临街的三处红瓦突出部。中央短屋顶与向南穿入里弄的通道相接。保护范围 OSM way 488963703 和北 1 门 POI 只用于对照街边位置。另一个北门点在保护边界以外。主楼段从照片和屋顶估宽 8.60 米、进深 7.25 米；外向约 334°，原点为街侧中央地面。底图最近的 1237、1266、2041 号建筑分别距门楼外包范围约 15.38、16.21、19.14 米，均保留原貌。第 21 级影像服务在此处返回无数据，定位采用第 19 级。[屋顶定位、各源距离与瓦片指纹](footprint-review.json) · [保护范围](https://www.openstreetmap.org/way/488963703)

[网页近景 GLB](../../../assets/models/candidates/jingan-bubbling-well-lane-gate/jingan-bubbling-well-lane-gate-web.glb) · [远景 GLB](../../../assets/models/candidates/jingan-bubbling-well-lane-gate/jingan-bubbling-well-lane-gate-lod.glb) · [原始 GLB](../../../assets/models/candidates/jingan-bubbling-well-lane-gate/jingan-bubbling-well-lane-gate-raw.glb) · [可编辑 Blender](../../../assets/models/candidates/jingan-bubbling-well-lane-gate/jingan-bubbling-well-lane-gate.blend) · [可旋转预览](../../../bubbling-well-lane.html)

## 原生重建

在 `projects/shanghai` 中执行。需要 Python、NumPy、Shapely 2.1 以上、FontTools、Node.js、Blender 4.3、gltfpack、ImageMagick 与 Open Image Denoise。原点在主拱临街中心，局部 X 向照片右手、Y 向弄内、Z 向上。网页 GLB 使用 glTF 的 Y 向上格式。

```sh
python -B source/precise/jingan-bubbling-well-lane-gate/source/build_model.py \
  --out /tmp/bubbling-assets --audit /tmp/bubbling-audit \
  --gltfpack gltfpack --oidn oidnDenoise
```

程序与原创建筑几何采用仓库 MIT 许可。字匾使用 Noto Serif CJK SC 的三个轮廓，随附改名字型子集和许可。参考照片未嵌入模型。[几何程序](source/gate_geometry.py) · [字体来源](source/fonts/provenance.json) · [字体许可](source/fonts/OFL.txt)
