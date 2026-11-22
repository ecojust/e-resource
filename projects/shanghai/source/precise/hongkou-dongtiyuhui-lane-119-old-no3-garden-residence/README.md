# 东体育会路119弄老3号花园住宅

第五批上海市优秀历史建筑名录按老门牌将这栋住宅列为5F026。2020年实拍的院门铜牌刻有“东体育会路／119弄老3号”，保护牌记载它建于1930年代，采用砖木结构，共两层。同弄22、23号另列5F004。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [院门及保护标牌，图41–42](https://www.thepaper.cn/newsDetail_forward_8327982)

从庭院看，楼上两樘木门通向带双回栏的阳台，旁边有一樘独立长窗。楼下两道拱窗共用螺旋柱和窗台，入口的叠涩托座支承多层灰色拱门套。木门分两列四排，上方另设扇形气窗。屋顶为四坡红瓦，两侧屋面在檐口附近转缓，庭院坡面有一座双光老虎窗。[2015年10月6日实拍](https://blog.sina.cn/dpool/blog/s/blog_5d1bdf480102w8ds.html)

沿弄一面下层有四道券窗，靠后角的两窗共柱。后转角另一面下层另有一对共柱券窗。两张从相反方向拍摄的照片可以辨出四樘巷侧上窗及穿过檐口的凸出竖井。藤叶覆盖了后墙上层，另侧院墙和树冠也遮住大部分外立面。该部分仅保留建筑围护轮廓。原始木门窗的安装年代、室内各房间和屋架尺寸仍待文献或测绘核实。[巷侧与转角的量测记录](measurements/lane-and-rear-opening-trace.json)

## 尺度与坐标

楼体采用局部坐标。X沿庭院正面向入口递增，Y自庭院入深，Z由入口门槛向上。以8.40米庭面宽作比例基准，用庭院端与后角照片的四个同名窗点、两组共23个庭面控制点和六道绕过转角的灰缝联合解算，进深取12.39米。改变各组观测的权重时结果在12.15至12.47米之间，逐个留出后窗点时为12.37至12.58米。单独依上层门窗或巷向灰缝求镜位，会分别得约11.10和13.08米。模型保留约半米的进深估计余量，绝对尺度尚待现场测绘。[跨角联合解](measurements/physical-corner-and-room-depth.json) · [两侧窗洞的同点量测](measurements/lane-and-rear-cameras.json) · [独立巷侧相机](measurements/independent-lane-camera.json)

正面按两个2015年庭院机位配准。第二机有50个同面特征，中位重投误差0.54个工作像素。2020年照片的院门挡住了楼下，只在上层开口选取控制点。各份核验保留实际首交、视线遮挡和跨机位误差。[庭院相机](measurements/registered-courtyard-cameras.json) · [铁栏取点](measurements/balcony-photographic-pixels.json)

## 制作文件

以Python及Shapely生成有厚度的墙身、窗框、门券、旋柱和铁栏，近远景使用各自的瓦口及曲线细分。外墙的砌缝是几何缝，两份表面纹理均为程序原创。各视角、照片出处及GLB复核脚本随源文件保留。

```sh
python source/build_model.py --output near.glb
python source/build_model.py --lod --output far.glb
python source/build_model.py --out export --audit review --blender blender --gltfpack gltfpack --oidn oidnDenoise
```
