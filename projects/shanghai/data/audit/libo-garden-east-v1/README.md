# 丽波花园东主楼

市房管局将吴兴路87号登记为第2D038项「丽波花园东主楼」，当时的使用单位为市体育研究所。现场保护牌记载赉安洋行设计、1928年竣工。衡复资料另载1940年，徐汇的两份资料也分别给出824与约1,150平方米的建筑面积。模型采用修缮后花园一面的照片，旧照里的敞廊和2014年餐厅时期的门窗各有记录。背面、被树木遮挡处以及未见测绘图的尺寸按影像比例估算。[市名录、现场牌和分期照片](../../../source/precise/xuhui-libo-garden-east-house/reference-review.json) · [逐图独立复核](independent-source-review.json) · [单体模型](../../../libo-garden-east.html)

南面保留错落的两组半露木山墙、四格阁楼窗和露台下五处落地开间。西侧阶梯状半圆挑窗、扇形瓦面、百叶与双通风孔烟囱另有侧面照片。原始网格与网页近景各17,176个三角面，远景9,720个。Blender原文件重开后可分别编辑76个网格。三档模型分别检查23条射线，覆盖门窗、山墙、瓦面、圆挑窗、烟囱与花园空地。[模型源文件](../../../source/precise/xuhui-libo-garden-east-house/source/build_model.py) · [原生重开与网格校验](geometry-native.json) · [69条表面探针](surface-probes.json) · [原生渲染](xuhui-libo-garden-east-house-preview.png) · [模型与照片的独立目检](independent-native-review.json)

2023年花园开放时的航拍能辨中央红瓦主屋和东端平顶附体。1948年图上，以相邻两排住房的八处端角校合后，主屋归入同一地块，现代屋顶边缘由三版正射影像与庭院照片确定。近景地物343切去474.96平方米并保留东端219.82平方米，远景相应为469.17和216.73平方米。沿裁线封回16.42米原生墙面，继续使用原地物约25.6米的概化高度。高瓦片的其余七个所有者及沿街办公楼652和衡山路排屋保留，吴兴路距裁片23.28米。[1948年平面](../../../source/precise/xuhui-libo-garden-east-house/historic-plan-fit.json) · [航片记录](../../../source/precise/xuhui-libo-garden-east-house/aerial-editions.json) · [原生近、远网格与截面](placement-geometry.json)

周边地物的真实底图高度与留存平顶参与了视线检查。用正式俯瞰相机按1280×800和390×844两种视窗分别检查六个识别点，均能看到南面山墙与窗带、西侧半圆体和烟囱。[相机与十二条视线](candidate-camera-sightlines.json) · [复核脚本](check-camera-sightlines.py)

备用矢量瓦片含23条建筑记录。公共绘制模块在编号147898520的2,426个轮廓中只裁一个，移去469.17平方米。其余2,425个轮廓、另外22条建筑记录以及独立办公楼保留。[备用瓦片原始字节与逐轮廓核对](vector-source-checks.json) · [217处已登记地标的重叠检查](existing-map-coverage-217.json)

前版217处目录与新登记的218处目录已分别核对。新场景实取1,245份已签资源，共1,089,921,047字节。桌面与手机的单体网页均切换近远景并完成四件下载。正式裁切和碰撞模块通过16个地面点及16项两类建筑源测试。[完整HTTP逐件校验](registered-http-218.json) · [前后目录与四件下载](actual-entry-and-four-downloads.json) · [运行模块实测](runtime-placement.json) · [桌面及手机记录](viewer.json)

## 普通地图入口与两端实拍

从前一版的217处地点切换至218处。手机从地点目录触屏选中并点击地图标牌，桌面从目录用鼠标选中，随后以键盘切换和返回。每次切换都核对模型、裁切范围和页面给出的地点名。[前一版同机位](city-31181/map-before.png) · [返回本楼](city-31181/map-returned.png)

下表按实际画面中各构件采样点的位置，统计位于画幅内且避开标牌和页面控件的点。单个点只代表该构件选定位置。

| 实拍 | 画幅 | 露出的采样点 |
| --- | --- | --- |
| [手机稳定画面](city-31181/map-mobile-same-camera.png) | 390×844 | 6/6 |
| [桌面稳定画面](city-31181/map-desktop-same-camera.png) | 870×660 | 6/6 |
| [手机公开加号](city-31181/map-mobile-public-zoom.png) | 390×844 | 5/6 |
| [细看立面](city-31181/map-street-facade.png) | 480×360 | 1/6 |
| [屋面](city-31181/map-roof.png) | 480×360 | 1/6 |

浏览器分别签收近景与远景模型，核对原有近、远底图，并实取四份文件。公开站整读1,247个文件，地面通行及周围楼房合计16个采样。对照、手机、桌面、键盘切走并返回、街面与屋面、远景六个独立会话均已结束，退出码均为0。[远档](city-31181/map-distant.png) · [各视图与遮挡位置](city-31181/default-screen-coverage.json) · [完整签收](city-31181/result.json)

[单体与下载页](../../../libo-garden-east.html) · [原始GLB](../../../assets/models/candidates/xuhui-libo-garden-east-house/xuhui-libo-garden-east-house-raw.glb) · [网页近景GLB](../../../assets/models/candidates/xuhui-libo-garden-east-house/xuhui-libo-garden-east-house-web.glb) · [远景GLB](../../../assets/models/candidates/xuhui-libo-garden-east-house/xuhui-libo-garden-east-house-lod.glb) · [Blender工程](../../../assets/models/candidates/xuhui-libo-garden-east-house/xuhui-libo-garden-east-house.blend)

在桌面870×660和手机390×844的普通目录画面里，可以同时辨认两组半露木山墙、花园侧五处落地开间、西边圆挑窗和烟囱。手机公开放大一档后，仍能看到屋面瓦色、烟囱、山墙木构和底层五个开间，圆挑窗的一部分出了画幅。480×360的街面与屋面近景中，地点卡占据画面中部，各只有一个构件采样点完全露出；两处近景保留原始控件。[手机公开放大](city-31181/map-mobile-public-zoom.png) · [桌面普通目录](city-31181/map-desktop-same-camera.png) · [各构件逐点覆盖](city-31181/default-screen-coverage.json)

初次前态检查在吴兴路底图尚未稳定时遇到 Chromium 渲染进程退出，未取得截图。首次返回码为1。上方列出的前态实图来自随后完成的单独检查。[首次浏览器记录](city-31181/initial-control-report.txt) · [首次退出记录](city-31181/initial-control-exit.txt)

第二次从东湖宾馆跨区移动至吴兴路也在底图稳定前退出，返回码为1。两次都没有形成可供比较的街景。完成的前态检查改由31180的公开坐标入口直接进入吴兴路，依次核对经纬度、高度及视角、地物343和原有邻屋。[第二次浏览记录](city-31181/second-control-report.txt) · [第二次退出记录](city-31181/second-control-exit.txt)

首次从公开坐标直接进入时，原底图已稳定，浏览器在读取画面状态时退出，尚未保存图片。随后在相同街区与同一机位减少浏览器绘制内存，并将前态与街面复查统一为480×360。[首次坐标入口浏览记录](city-31181/third-control-report.txt) · [该次退出记录](city-31181/third-control-exit.txt)

在披露的远景视图中，首次退至地图缩放15.65时，眼点高671.6米，模型仍保持近档。通过页面的减号实点一次后，缩放降至14.65，距离越过本楼的820米远档阈值，浏览器实际换用9,720个三角面的远景文件。[公开减号点击记录](city-31181/public-distant-zoom.json) · [远景画面与加载记录](city-31181/segment-distant.json)
