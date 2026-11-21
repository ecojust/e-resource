# 海格公寓花园立面核验

2025年修缮正照中有四列七层弧顶阳台，入口匾额下是一对深置的门扇。两端石柱各支承三跨敞廊。近景和远景分别有83,028和53,364个三角面。三个交付网格各通过159条射线，覆盖28扇弧顶窗、阳台栏杆、石廊两根独立柱与可见深度、门匾下实际空洞、门扇和四处屋面高度。已重新打开Blender文件并比对近景材质及有向三角面。 [原始和解码几何](surface-checks.json) · [Blender复核](geometry-native.json)

离草坪最近的1554号南壁由独立切片替换。旧建筑近景投影保留78.70%，远景保留78.90%。西邻455号与切片实际相距4.58／4.65米，上海宾馆2395号相距27.59／27.69米。地面17处证据覆盖草坪、墙脚与中央入口门槛，另核手机、桌面各七个可见构件。 [落位](placement-geometry.json) · [默认视线](overview-sightlines.json) · [模型接入合同](final-placement-contract.json)

[来源和重建边界](../../../source/precise/jingan-haig-apartments-garden-front/README.md) · [模型清单](../../../assets/models/candidates/jingan-haig-apartments-garden-front/manifest.json) · [单体查看](../../../haig-apartments-garden.html)

[四视图与四种实际下载](viewer.json)

[原生图目视核对](visual-review.json)

[25k所选构件、文件与正式目录](25k-compatibility.json) · [23k实体接入](runtime-placement.json)

[三版完整HTTP核验](full-served-inputs.json)

## 普通地图入口与两端实拍

从前一版的243处地点切换至244处。手机从地点目录触屏选中并点击地图标牌，桌面从目录用鼠标选中，随后以键盘切换和返回。每次切换都核对模型、裁切范围和页面给出的地点名。[前一版同机位](city-31207/map-before.png) · [返回本楼](city-31207/map-returned.png)

下表按实际画面中各构件采样点的位置，统计位于画幅内且避开标牌和页面控件的点。单个点只代表该构件选定位置。

| 实拍 | 画幅 | 露出的采样点 |
| --- | --- | --- |
| [手机稳定画面](city-31207/map-mobile-same-camera.png) | 390×844 | 7/7 |
| [桌面稳定画面](city-31207/map-desktop-same-camera.png) | 870×660 | 7/7 |
| [手机公开加号](city-31207/map-mobile-public-zoom.png) | 390×844 | 5/7 |
| [细看立面](city-31207/map-street-facade.png) | 480×360 | 3/7 |
| [屋面](city-31207/map-roof.png) | 480×360 | 1/7 |

浏览器分别签收近景与远景模型，核对原有近、远底图，并实取四份文件。公开站整读1,459个文件，地面通行及周围楼房合计22个采样。对照、手机、桌面、键盘切走并返回、街面与屋面、远景六个独立会话均已结束，退出码均为0。[远档](city-31207/map-distant.png) · [各视图与遮挡位置](city-31207/default-screen-coverage.json) · [完整签收](city-31207/result.json)

[单体与下载页](../../../haig-apartments-garden.html) · [原始GLB](../../../assets/models/candidates/jingan-haig-apartments-garden-front/jingan-haig-apartments-garden-front-raw.glb) · [网页近景GLB](../../../assets/models/candidates/jingan-haig-apartments-garden-front/jingan-haig-apartments-garden-front-web.glb) · [远景GLB](../../../assets/models/candidates/jingan-haig-apartments-garden-front/jingan-haig-apartments-garden-front-lod.glb) · [Blender工程](../../../assets/models/candidates/jingan-haig-apartments-garden-front/jingan-haig-apartments-garden-front.blend)

海格主楼的七项取景目标覆盖门厅、东西券廊、两翼阳台、中央高墙和东侧山墙。17处地面和5栋邻屋逐点核对。正式31207单体页面另实拍桌面、手机各两档并实际保存四件文件。[两端四图与下载散列](city-31207/standalone/viewer.json) · [两代签名与视线登记](city-31207-signed-inheritance.json) · [地图十一个时刻的关闭凭据](city-31207/207-map-slot-released.json)

首次前态截图已生成。复核相机脚本时，私有对照文件长3,163字节，正式HTTP文件长4,316字节，会话退出码为1。随后从两代各自的正式URL逐件固定页面和浏览脚本，复测前态正常退出；两次前态图片的SHA-256相同。[首次实测记录](city-31207/initial-control-runtime/control-browser-original.txt) · [初次退出原件](city-31207/initial-control-runtime/exit-original.txt) · [两代运行文件](city-31207/initial-control-runtime/verified-runtime.json)

第一轮桌面已在870×660画幅形成两张图，随后渲染器在点击地图标牌前中断，进程退出码为1。采用单进程软件渲染重新打开相同入口，保留尺寸、机位和检查条件，实测鼠标点击命中本楼。[首次两图和中止记录](city-31207/initial-desktop-renderer/original-report.txt) · [首次退出凭据](city-31207/initial-desktop-renderer/original-exit.txt) · [复拍与鼠标输入](city-31207/segment-desktop.json)

海格公寓与高安公寓直线相距约1.49公里。首轮通过键盘切到高安后，等待海格退出显示的检查超时。复测确认两栋模型及各自裁切此时都保留；再用键盘切到虹口东大名路378号，海格才退出显示和裁切。键盘返回海格后，花园立面重新出现。[首轮超时的原始报告](city-31207/nearby-return/initial-report.txt) · [三个目录选择及实际状态](city-31207/segment-return.json)

高安公寓普通机位中心距海格锚点实测1,493.08米。海格登记距离为1,200米，已显示物体另有300米保留范围，两座公寓同时出现符合此处的实际距离。[机位、两栋裁切与运行条件](city-31207/nearby-return/retained-nearby-visibility.json)

480×360的街面和屋面截图保留了地点卡。卡片盖住门厅及下部立面，窄幅近景只露出阳台栏杆、窗格的一部分。另从正式目录以鼠标打开830×820地图，保留同一页面控件，分别拍摄东西端敞廊、中央门厅和屋顶。东西端可分出两根石柱、三跨栏杆与后退的暗部，门厅可见外凸拱罩与洞口，地点光点遮住门洞下部。较高的全景可同时看见四列阳台、两处高起屋面和与后方旧楼相接的位置。[西端券廊](city-31207/garden-details/garden-west-loggia.png) · [东端券廊](city-31207/garden-details/garden-east-loggia.png) · [门厅](city-31207/garden-details/garden-entrance.png) · [屋面与全立面](city-31207/garden-details/garden-upper-balconies.png) · [实拍及各点的界面遮挡](city-31207/garden-details/main-browser.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/9977b91a7b26eb58696f67834a7d4462ba2720ff/projects/shanghai/index.html#landmark=jingan-haig-apartments-garden-front&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
