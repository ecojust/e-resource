# 永福路151号住宅南立面

市房管局第二批名录以2D023登记永福路151号。徐汇区文化部门的历史建筑资料记载1941至1942年建造，建筑师为杨增华。以区级公开外观照和2013年5月19日独立拍摄的外观、铭牌照片核对同一南立面。永福路181号另一处1935年住宅的资料与本栋分列。原始来源、照片日期与建筑辨识见 [来源说明](../../../source/precise/xuhui-yongfu-road-151-south-front/README.md)。

可编辑工程和三档GLB复原照片所见的西侧弧形环廊、中部退入的阳台与曲线女儿墙，以及东侧上下各三扇拱窗。螺旋柱、铁栏、叠涩檐和浅台阶都采用有起伏的实体几何。侧面进深与位置按公开影像估算。交付范围止于南立面及其可见转折。

原生工程已重开并渲染；三档文件的实际三角面通过90项表面与天空射线核查。玻璃面比窗框后退，西侧顶层环廊在柱后保留约3米纵深。见 [原生核验](geometry-native.json)、[射线结果](visible-surfaces.json) 和 [渲染](xuhui-yongfu-road-151-south-front-preview.png)。

城市配准使用地块1519的近远两档原始网格。切去南立面占用部分后，原生近景、远景投影面积分别保留95.20%与95.39%，裁口与其他建筑的实测最小间隔为19.24米。场地与高程属近似复原。见 [配准核查](placement-geometry.json) 和 [正式登记](final-placement-contract.json)。

正式城市版本从206处增至207处。前一版的每条模型记录都原样保留，1157个清单文件经正式HTTP实取共1,044,318,127字节。新版运行时核对地面与邻屋点、两类矢量地物及1519号原生源的定向裁剪。[前后实际比对](renderer-parent-controls.json) · [运行时原始结果](runtime-placement.json) · [逐文件实取](renderer-release-http.json)

独立页从正式207处版本打开，桌面和390像素手机均实测近、远两档及四件下载；西侧半圆窗廊、中央两扇上窗和东侧六扇拱窗在两档均可辨识。[独立页记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png)

### 正式城市地图复核

从206处旧城的同地块进入207处新版，1280像素桌面以鼠标、390像素手机以触屏从目录选中永福路151号。两端默认画面都可辨西侧分格弧廊、中央两道阳台铁栏和东侧两排拱窗。窄屏里东侧窗组较小。近看庭院时能读到环廊竖框、上层柱和阳台的进深，右端部分窗组在该幅之外。[桌面默认](city-31170/desktop/map-desktop.png) · [手机默认](city-31170/phone/map-mobile.png) · [庭院近景](city-31170/architecture/map-garden-terrace-and-windows.png)

同机位前后对照保留了住宅后方的相邻楼体。街面、屋面、远景和手机放大均完成实拍，16个地面测点及四件模型下载通过。第一次旧城实测遇到浏览器渲染进程中断，原日志和同址重跑结果均已保留。[同地旧景](city-31170/before/map-before.png) · [地面实测](city-31170/desktop/main-browser.json) · [远景与下载](city-31170/distant/main-browser.json) · [实图判读](city-31170/visible-architecture.json) · [首次中断记录](city-31170/first-control-interruption/log-proof.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/88cd37ba7eb2101d5848a2f39c20d37b317ee033/projects/shanghai/index.html#landmark=xuhui-yongfu-road-151-south-front&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，12 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
