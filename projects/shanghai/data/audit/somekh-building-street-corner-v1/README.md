# 沙美大楼街面模型核验

北京东路190号的主入口和东南转角圆廊是两个门。北京东路的双柱托起卷涡断山花，楼梯间沿主门轴向上升起。四川中路一侧可从圆廊外缘进入两根柱之间，走到弧形玻璃门前。模型覆盖北京东路九个窗轴和四川中路紧邻转角的一跨；敞开的鼓座保留朝街可见的三只拱窗。鼓座背面、未摄角度及若干尺寸含估计。[身份与来源](../../../source/precise/huangpu-somekh-building-street-corner/README.md) · [主入口](preflight/central-portal.jpg) · [圆廊](preflight/corner-porch.jpg) · [鼓座俯视](preflight/drum-from-above.jpg)

三档网格分别有103,260、103,260、64,320个三角面。每档从133个位置向实际表面投射，检查了南面退进窗、门窗开口、角柱、锻铁阳台和露天鼓座。相机预检对照原城市网格，在桌面和手机视口分别核对14个构件点。[制作记录](preflight/model-review.json) · [实物首交](preflight/visible-feature-probes.json) · [相机视线](preflight/camera-sightlines.json) · [北京东路立面](preflight/beijing-front.jpg)

原城市建筑251与OSM 446937294相符。首层沿墙口局部裁切后，近档保留原足印约91.41%，远档保留约91.73%。二层及以上有两段露台向内退进，上层裁片从距铺面6.05米处起，与首层边界在水平方向重叠5毫米，原楼16米以上没有待裁表面。地面保留首层边界，加入庭柱、街墙和门扇的实际阻挡。三个网格各有79个地面核点，包含圆廊可走处、柱身、门后和24座独立邻屋。对OSM聚合矢量和Overture建筑又分别复算，并比较近、远档的卸载与重新载入。[地面截线](preflight/ground-sections.json) · [首层原楼](preflight/owner-and-lower-cut.json) · [退进上层](preflight/upper-cuts.json) · [原矢量与地面](preflight/vector-ground.json) · [近远档重载](preflight/runtime-cut-texture.json)

## 北京东路和四川中路的实景地图核对

桌面与手机各从地点目录进入沙美大楼，再用鼠标和触摸从恒丰大楼切换过来。地图中的九轴窗墙向四川中路转折，楼梯间在中央抬高，敞开的鼓座位于右端。部分窗轴被地图地点标签遮住，放大北京东路190号主门后能看到卷涡断山花与两旁石柱，门槛仍有一部分被地点卡覆盖。[北京东路立面](final-map-31268/architecture/map-street-facade.png) · [主门](final-map-31268/architecture/map-beijing-190-portal.png) · [四川中路转角](final-map-31268/architecture/map-corner-porch-and-open-drum.png)

七次地图操作留存十三幅画面，另从独立建筑页保存六幅。地图复核了79处地面，包括24座邻屋。第一次手机校准时，浏览器把九像素的标记缩至三像素。校准页面采用设备宽度后，390×844视口上下两角均与实际显示栅格吻合。[逐图观察](final-map-31268/visual-review.json) · [独立页俯视](final-map-31268/standalone/viewer-desktop-full-above.png)
