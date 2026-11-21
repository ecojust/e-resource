# 盖司康公寓主楼南立面核验

市房管局两份原表分别把十三层主楼与五层街边辅楼登记在1202号、1204至1218号。南面高位、仰视及入口近照用来核定退台、两组双列阳台、三条竖带、弧角雨篷和石阶。[史料与原图](../../../source/precise/xuhui-gascogne-apartments-main-building/README.md) [独立查看](../../../gascogne-apartments-main.html) [两栋地块图](registered-buildings.png)

近景原始和网页各36,960面，远景26,208面。原生工程重新打开后逐材质比较真实面片；近远两种网页模型均实际解压。三档各237项射线检查中，每个阳台跨分别检验开口、深处钢窗和前缘，另核验双门凹口、五级石阶、三扇雨篷透光板、中央竖带、层层后退的屋面。[原生工程与解码比对](geometry-native.json) [逐档射线明细](surface-checks.json) [四件下载](../../../assets/models/candidates/xuhui-gascogne-apartments-main-building/manifest.json) [原生渲染](xuhui-gascogne-apartments-main-building-preview.png)

地图上只替换来源107的南面，底图主楼近景保留74.53%，远景保留74.69%。20个地面点检验双入口及门槛、石阶、前院步行空间、实体墙及后部保留体量。裁切与街面辅楼4703近景相距25.90米，远景相距25.98米。桌面和手机分别由默认机位检查七条到门、冠、阳台的视线。[原生近远网格与地面](placement-geometry.json) [最终落位](final-placement-contract.json) [双屏默认机位](overview-sightlines.json)

[照片与原生图对照](visual-review.json)

[双端四图及真实下载](viewer.json)

[正式城市场景前后态实际HTTP](signed-23k-http.json)

[全城裁片与地面实测](runtime-placement.json)

[三版完整HTTP核验](full-served-inputs.json)

## 南院的城市实景

从桌面和手机的普通目录进入主楼，可以看清两边成对的露廊、中央三道竖肋和逐级退下的屋顶。俯视入口时，雨篷内三片玻璃和弧形石阶清楚可见。低机位另拍到雨篷下两个后退的入口及其间的黑色石墙。地点灯牌遮住石墙右上部。[南院手机全景](city-31205/map-mobile.png) · [屋顶退台](city-31205/map-roof.png) · [雨篷和石阶](city-31205/map-garden-doors-and-canopy.png) · [雨篷下的双入口](city-31205/map-twin-doorways-beneath-canopy.png)

两代城市地图与桌面、手机独立查看器共核对15幅画面，另实测25处地面，包含五幢相邻建筑。四件文件均从实际页面保存并核对字节。[逐图说明](city-31205/visual-review.json) · [实照对读](city-31205/independent-photo-comparison.json) · [两端独立查看及下载](city-31205/standalone/viewer.json) · [各阶段退出记录](city-31205/slot-released.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/cd5f162df93688f3da40f3e1a8a33b7c1750f84e/projects/shanghai/index.html#landmark=xuhui-gascogne-apartments-main-building&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
