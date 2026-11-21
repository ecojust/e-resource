# 外滩信号台现址塔身、号杆与站房

市房屋管理局第二批登记2A011，对应外滩信号台。2019年现场铭牌可辨中山东二路1号甲、1907年建造、1993年整体向东南移动20余米。2015年和2022年的实拍分别显示西北塔基、塔身、信号横桁和东南站房。两期航片能辨塔位于站房西北端。参考记录含十张Commons照片的文件页、实读取图尺寸、来源署名和校验值。[门牌、迁移与建筑照片](../../../source/precise/huangpu-bund-signal-tower/reference-review.json) · [制作范围](../../../source/precise/huangpu-bund-signal-tower/README.md)

原生场景重开后有48组可编辑网格，原始及网页近景各25,184个三角面，远景21,328个。实测高度47.40米为按影像估算的模型值。三档各有27条射线核对站房券门、门扇玻璃、铭牌位置、红白砖带、塔基和平台、三条红色腰带、信号杆、横桁和索具。两处东南角在首次预览中有深色接缝，已补入实照可辨的浅色转角石带。[首次预览](preflight/station-first.png) · [最终原生渲染](huangpu-bund-signal-tower-preview.png) · [原生重开](geometry-native.json) · [表面实测](surface-checks.json)

现址底图589与带保护编号的OSM建筑440730276第4版交并比97.64%。城市场景旧近、远两档都是估高6.40米的普通房屋，远景足迹146.20平方米。最终模型地面接触148.48平方米，展示裁剪169.14平方米，最近的邻栋1707在近档离裁面43.93米，四邻的两档均完整保留。15栋外滩精建的模型包围范围距此至少85.43米，27处步道和3,479件街具分别距此至少22.73米与29.97米。对外滩现有街景网页网格另查全部138,930面，最近的一处是离塔房足迹22.41米、高3.5厘米的铺石。254处目录中最近的精建范围仍有65.02米。[双档城市场景与地面点](placement-geometry.json) · [既有模型、步道与街具](prior-model-coverage.json) · [街景逐面核对](bund-street-mesh.json) · [两个屏幕的八处视线](camera-sightlines.json)

单体页的桌面和手机分别实拍了正面近景、站房斜视和正面远景。站房斜视能同时看到附楼窗列、圆塔基与号杆。手机全貌图中最细的杆索对比弱，门牌文字也不能辨读。四个下载均由浏览器保存，并与交付清单逐一核对字节和SHA-256。[查看器实拍与四件下载](viewer.json) · [桌面斜视](viewer-desktop-station-and-tower.png) · [手机斜视](viewer-mobile-station-and-tower.png) · [与原照复核](visual-review.json) · [单体页面](../../../bund-signal-tower.html)

在真实258处前版目录再次检查，外滩既有模型中，最接近本站的是法国邮船公司大楼。该楼的放置范围距信号台足迹65.02米，保留同一城市网格组内的原所有者863。外白渡桥也在此次完整前序目录中，实体包围范围与站房分开。[最终前版与既有模型复核](final-prior-coverage.json)

外滩信号台由上版258处递增为259处。前版1,561个签名文件和新版1,569个原始签名文件均已逐项复算。对最终地图前后两版的目录、相机入口和原底图近远景分别发起了HTTP请求，本版另核对了单体页、查看器脚本、模型清单和四个下载。最终站完整读取1,586项、1,323,960,381字节，核对每项校验值并复查五个范围请求。[逐层目录与生成器核验](signed-stations/26k-comparison.json) · [27层桥面步行核验](signed-stations/27k-navigation.json) · [最终站全量HTTP](signed-stations/28k-all-http.json) · [两版实际资源与四件下载](signed-stations/real-28k-predecessor-and-new-building.json)

## 普通地图入口与两端实拍

从前一版的258处地点切换至259处。手机从地点目录触屏选中并点击地图标牌，桌面从目录用鼠标选中，随后以键盘切换和返回。每次切换都核对模型、裁切范围和页面给出的地点名。[前一版同机位](city-31222/map-before.png) · [返回本楼](city-31222/map-returned.png)

下表按实际画面中各构件采样点的位置，统计位于画幅内且避开标牌和页面控件的点。单个点只代表该构件选定位置。

| 实拍 | 画幅 | 露出的采样点 |
| --- | --- | --- |
| [手机稳定画面](city-31222/map-mobile-same-camera.png) | 390×844 | 6/8 |
| [桌面稳定画面](city-31222/map-desktop-same-camera.png) | 870×660 | 8/8 |
| [手机公开加号](city-31222/map-mobile-public-zoom.png) | 390×844 | 5/8 |
| [细看立面](city-31222/map-street-facade.png) | 480×360 | 1/8 |
| [屋面](city-31222/map-roof.png) | 844×636 | 3/8 |

浏览器分别签收近景与远景模型，核对原有近、远底图，并实取四份文件。公开站整读1,586个文件，地面通行及周围楼房合计17个采样。对照、手机、桌面、键盘切走并返回、街面与屋面、远景六个独立会话均已结束，退出码均为0。[远档](city-31222/map-distant.png) · [各视图与遮挡位置](city-31222/default-screen-coverage.json) · [完整签收](city-31222/result.json)

[单体与下载页](../../../bund-signal-tower.html) · [原始GLB](../../../assets/models/candidates/huangpu-bund-signal-tower/huangpu-bund-signal-tower-raw.glb) · [网页近景GLB](../../../assets/models/candidates/huangpu-bund-signal-tower/huangpu-bund-signal-tower-web.glb) · [远景GLB](../../../assets/models/candidates/huangpu-bund-signal-tower/huangpu-bund-signal-tower-lod.glb) · [Blender工程](../../../assets/models/candidates/huangpu-bund-signal-tower/huangpu-bund-signal-tower.blend)

信号台的附楼南门、南侧窗、北端圆室、低层环廊、塔身两道砖带、塔顶环廊与风向杆共八处实物进入取景核对。13处地面采样和4栋邻屋逐点复查。同一近景分组保留原有863号，加入589号的两片裁切。另从正式31222单体页在桌面和手机分别拍摄全楼、附楼与塔、远档三景，并实际保存四件文件。[独立页六图和四份下载](city-31222/standalone/viewer.json) · [正式站与前代的签名](city-31222-signed-inheritance.json) · [地图十一帧实拍与退出回执](city-31222/222-map-slot-released.json)

两张480×360专项图中，打开的详情卡片遮住了塔身大部。放宽屋顶画幅后，环廊、栏杆、桅杆及其与附楼的位置关系可以辨认，上部仍有一段被地点标牌挡住。第三次实测取得两张街面图，第八次取得宽幅屋顶图，第九次核对全部17个地面点；第十次在实际发起近、远两组源文件请求后，核完原城模型与裁切。远景从两次公开缩放中得到，实测距模型2186米，超过1100米的远档阈值；当时的单体标牌已聚合，信息卡仍选中信号台。完整的远景会话复用了首次实拍与场景签名，另从正式站逐字复核四份模型资源。各次中止的画面、原始报告、实际退出与成功补测分别保留。[现场记录与原始截图](city-31222/attempts/index.json) · [逐图目检](city-31222/manual-visual-review.json)
