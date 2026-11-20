# 大胜胡同德莱蒙德住宅南向花园立面

华山路263弄7号的庭院北侧，红砖门廊夹在两座半木构三角山花之间。三开间立面向院中突出，两侧上下层敞廊向后退进。2014年和2022年的庭院照片可对应这组关系。2014年2月的里弄街面照片拍到其他住宅。屋面坡度、廊深、栏杆及石饰的尺寸根据照片和航片估算。[历史、门牌与照片](../../../source/precise/jingan-dasheng-drummond-residence/README.md) · [航片与错位的门牌兴趣点](../../../source/precise/jingan-dasheng-drummond-residence/garden-roof-registration.json) · [独立模型](../../../dasheng-drummond-residence.html)

可编辑文件按构件保存73个网格、14种材质。Blender 4.3.2重开后按材质逐面与原始GLB比对，并从该场景输出庭院立面图。网页近景及原始版各59,124个三角面，远景12,688面。对照原照片后调低两侧山花、校正坡瓦位置，恢复中央石阶矮墙的盲拱进深，并让四扇门在上下两层敞廊背后可见。从三份最终文件各测44处，包括门窗、女儿墙透孔、三处屋面、石阶及球饰。[原生图](jingan-dasheng-drummond-residence-preview.png) · [初稿图](preflight/first-native.png) · [原生与三档资产比对](geometry-native.json) · [132次实物检查](portico-checks.json) · [四件交付文件](../../../assets/models/candidates/jingan-dasheng-drummond-residence/manifest.json)

城市源1355覆盖庭院北侧的住宅及后侧建筑。将三份最终GLB的投影与已有源轮廓相交，沿门廊和两侧山花分别开出3块，保留三段之间的原楼。原近景和远景分别保留91.94%与92.09%，原楼与已建部分的残余投影交叠均低于0.00001平方米。源模型给出的屋顶高度为25.83米，剖开处按源高收口。17个地面检查点包括草地、石阶、矮墙、门廊、后厅和五个独立邻楼，落有263弄7号兴趣点的3904整栋保留。[放置与边界](final-placement-contract.json) · [各源网格、剖口及地面实测](placement-geometry.json)

桌面1250×820与手机390×844均从独立页切换近远景，两侧廊、中央门廊前后关系和台阶在4张截图中可辨。下载的网页近景、远景、原始版和Blender文件与各自SHA-256一致。全城机位另用112组角度检查13,641个立面采样点，方位−18°、俯角60°时，保留的城市近远源均未遮住自身可见的采样点。主图浏览器复核另行记录。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机远景](viewer-mobile-lod.png) · [四件下载与浏览](viewer.json) · [城市几何下的相机角度对照](camera-preflight.json)

191处原始冻结站从前一版本190处继承，旧目录中的地标记录逐项相同，1,018次实际HTTP下载共978,481,656字节。正式版城市渲染模块在目标附近新增9个裁片，全城共1,001片、20个宏区，峰值322片；门廊对应的近景组只处理1355，其他地块和另一个近景组保持原样。[冻结文件与来源](frozen-http.json) · [正式运行模块与地面检查](runtime-placement.json)

独立页斜向按钮改为“门廊与庭院石阶”。更名前后的三档GLB与Blender下载逐件相同。桌面与手机重新检查近远档，再从正面实际点击该按钮并记录视角变化。[新旧页面及四件哈希](viewer-label/caption-change.json) · [新版四个视图](viewer-label/viewer.json) · [桌面斜视](viewer-label/oblique-desktop.png) · [手机斜视](viewer-label/oblique-mobile.png)

自本栋首次登记的版本起，摄影角度按钮显示“门廊与庭院石阶”。从第154项至第162项逐版签收，原站与六个后续运行层均从HTTP读回修正页。原有模型及目录的摘要一致。[本栋实取页面](villa-viewer-caption-http.json) · [修改范围与归档摘要](viewer-caption-correction/summary.json) · [原页面和历次签名](viewer-caption-correction/superseded-signatures.tar.xz)

正式191处城市站逐件复读更名后的页面、公共浏览器模块、模型清单与四件下载。[正式站7项HTTP](viewer-label/production-http.json)

正式主图从190处增至191处。在同一庭院机位，登记前是一面连续的通用建筑外墙，登记后可看到中央红砖门廊、两侧三角山花、上层敞廊及门前石阶。手机从目录点入，桌面鼠标与手机触屏也分别从上一处住宅点选了本栋灯牌。全城缩放下已实取远景文件。地面22次抽查中，草坪小径、弧墙前方和两侧廊前空地均可走，矮墙、石阶与保留的后厅均有阻挡。近远景的10段原有建筑切面分别核实。首次取回两个原始底图文件时上游返回502，随后按原有提交取回相同字节，在两期实测站点逐件复核。[同机位登记前](city-24154/before/map-before.png) · [手机目录进入](city-24154/after/map-mobile-settled.png) · [门廊与石阶](city-24154/after/map-portico-stair.png) · [侧廊与山花](city-24154/after/map-gabled-gallery.png) · [地面和远景文件](city-24154/after/main-browser.json) · [原始底图取回记录](city-24154/input-recovery.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/0a5756e1fe5d114d68aed34a1e5092af9328a653/projects/shanghai/index.html#landmark=jingan-dasheng-drummond-residence&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
