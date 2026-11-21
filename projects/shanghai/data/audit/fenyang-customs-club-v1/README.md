# 汾阳路海关俱乐部木屋

市房管局第2D045项登记为「住宅」，门牌汾阳路9弄3号。2017年的现场保护牌同时标注1898年建造、砖木结构及英文 Wood House of Customs Club。地方报道把它记为与赫德有关的俱乐部或旧宅。模型呈现2017、2018及2020年影像中高出庭院的方柱南廊、中央阶梯、水平木板和灰色复合屋顶。后墙窗位、板缝的间距和整体尺寸皆按影像估算。[史料与逐图来源](../../../source/precise/xuhui-fenyang-customs-club/reference-review.json) · [现场铭牌与照片的独立复核](independent-source-review.json) · [查看单体](../../../fenyang-customs-club.html)

南坡中央只有一座三面凸出的翘檐窗。东坡两扇小窗、西坡一窗和靠近西北角的方形尖塔分别建模。近景和原始网格各50,956个三角形，远景21,224个，重开Blender有102个可编辑网格。共75条表面探针核对方柱、板壁、门廊、石阶、绿窗、塔和分层屋面。[原生网格与文件校验](geometry-native.json) · [三档几何探针](surface-probes.json) · [原生图](xuhui-fenyang-customs-club-preview.png) · [独立图像复核](independent-native-review.json)

三期正射影像、南侧院内的DJI俯拍及文汇照片共同定位到地物784。具名地点标记落在其西边，地面落位按真实底图轮廓和各期屋面。近景与远景分别替换324.11、319.05平方米；同组其余20栋保留，最近邻楼网格距裁面1.72米。汾阳路距裁面69.32米。备用瓦片41项中，编号38934830的3,535个部件仅去掉木屋对应的319.06平方米。南部院落、北面红屋顶公寓和西侧小屋继续保留。[三期航片](../../../source/precise/xuhui-fenyang-customs-club/aerial-editions.json) · [具名地点与底图坐标](../../../source/precise/xuhui-fenyang-customs-club/footprint-review.json) · [实网格、碰撞与备用源](placement-geometry.json) · [正式模块实际裁切](vector-source-checks.json) · [226处旧地标](existing-map-coverage-226.json)

手机390×844和桌面1280×800均采用花园东南方向取景。按周边楼面实际高度，各屏幕到前廊、阶梯、腰窗和右侧开窗的六条视线均通畅。俯角34度可看见南廊上方凸窗与屋顶层次。[默认相机与十二条视线](candidate-camera-sightlines.json)

226处与227处两版入口均实际读取。最终场景逐项取得1,319份资源、1,128,536,846字节。独立页在桌面和触屏切换近远景，四件下载逐个核对。正式几何模块通过29个地面点与42个两源测试。[逐文件HTTP](registered-http-227.json) · [新旧目录与下载](actual-entry-and-four-downloads.json) · [运行模块](runtime-placement.json) · [桌面和手机](viewer.json)

## 普通地图入口与两端实拍

从前一版的226处地点切换至227处。手机从地点目录触屏选中并点击地图标牌，桌面从目录用鼠标选中，随后以键盘切换和返回。每次切换都核对模型、裁切范围和页面给出的地点名。[前一版同机位](city-31190/map-before.png) · [返回本楼](city-31190/map-returned.png)

下表按实际画面中各构件采样点的位置，统计位于画幅内且避开标牌和页面控件的点。单个点只代表该构件选定位置。

| 实拍 | 画幅 | 露出的采样点 |
| --- | --- | --- |
| [手机稳定画面](city-31190/map-mobile-same-camera.png) | 390×844 | 6/6 |
| [桌面稳定画面](city-31190/map-desktop-same-camera.png) | 790×535 | 6/6 |
| [手机公开加号](city-31190/map-mobile-public-zoom.png) | 390×844 | 6/6 |
| [细看立面](city-31190/map-street-facade.png) | 408×550 | 3/6 |
| [屋面](city-31190/map-roof.png) | 408×550 | 0/6 |

浏览器分别签收近景与远景模型，核对原有近、远底图，并实取四份文件。公开站整读1,321个文件，地面通行及周围楼房合计29个采样。对照、手机、桌面、键盘切走并返回、街面与屋面、远景各分段均已结束。街面和屋顶分作两次独立会话，其余各分段各有一次完成的会话，退出码均为0。[远档](city-31190/map-distant.png) · [各视图与遮挡位置](city-31190/default-screen-coverage.json) · [完整签收](city-31190/result.json)

[单体与下载页](../../../fenyang-customs-club.html) · [原始GLB](../../../assets/models/candidates/xuhui-fenyang-customs-club/xuhui-fenyang-customs-club-raw.glb) · [网页近景GLB](../../../assets/models/candidates/xuhui-fenyang-customs-club/xuhui-fenyang-customs-club-web.glb) · [远景GLB](../../../assets/models/candidates/xuhui-fenyang-customs-club/xuhui-fenyang-customs-club-lod.glb) · [Blender工程](../../../assets/models/candidates/xuhui-fenyang-customs-club/xuhui-fenyang-customs-club.blend)

第一次桌面运行取得两张真实画面并点中地图标记。结束时，私有验收目录通过软链接读到了改变中的工作树相机脚本，末次输入比对退出1。31189、31190的相机实取均为 `73e4c91277cb4f07db11dda2ebfb78ccd5dcd11d2f266ff7eacd9ea201784845`，与两代正式签名一致。将验收指针固定到逐字校过的文件后，从桌面分段重新运行。[第一次原始报告](city-31190/first-desktop-input-check/browser-report.json.txt) · [实际退出记录](city-31190/first-desktop-input-check/actual-exit.json.txt) · [两代18项正式输入复核](city-31190/first-desktop-input-check/fixed-official-inputs.json)

第一次街面与屋顶专项保存了街面和门廊两张图。Node退出码为0，但在第三个视角结束前关闭，原报告保留 `completed: false`。复验在两次408 × 550浏览器会话分别完成街面和绿门、屋顶和折面老虎窗。每次保存两张图后正常退出，最后一次同时核对地面及邻楼。[初次未完成报告](city-31190/architecture-sessions/first-incomplete-report.json.txt) · [街面复验](city-31190/architecture-sessions/street-report.json) · [屋顶与地面复验](city-31190/architecture-sessions/roof-report.json) · [实测进程退出](city-31190/architecture-sessions/observed-processes.json)

远档切换距离为820米。第一次在817.16米点击地图公开缩小按钮，渲染进程中止。随后两次会话分别达到894.41米和877.52米，均未保存截图，退出码为1。第四次以340 × 270画幅进入877.52米，在页面确认载入远档后保存浏览器原帧，正常退出。远景画面中央由地点卡片遮住，建筑细部以门廊近景和单体页为准。[三次退出与最终距离实测](city-31190/distance-sessions/distance-comparison.json) · [远档原帧](city-31190/map-distant.png)

默认手机及桌面可以辨出整体坡屋顶和平面，画面中的近邻建筑会挡住局部。手机再点一次公开加号，前方浅色楼体遮住中部。街面视角可见门廊窗扇和绿门一部，屋面近景的标牌与地点卡遮住中央老虎窗。另以540 × 610画幅从花园侧补拍，近邻灰屋面遮住此栋，保留原帧供比较。单体页可旋转对照老虎窗、门廊与入口的相对位置。[街面门廊](city-31190/map-street-facade.png) · [花园侧遮挡对照](city-31190/garden-approach/map-garden-porch-and-dormers.png) · [补拍报告](city-31190/garden-approach/main-browser.json) · [全部浏览器退出记录](city-31190/garden-approach/190-map-slot-released.json) · [单体页](../../../fenyang-customs-club.html)
