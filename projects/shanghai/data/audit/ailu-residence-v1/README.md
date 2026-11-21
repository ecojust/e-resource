# 爱庐甲楼花园敞廊核验

两张原图由同一位作者用同一支18毫米镜头拍摄。甲楼的原始时间为2015年7月18日18时18分09秒，乙楼为18时18分37秒。甲楼的灰色庭面有一处大宽券和较低的西侧敞廊，乙楼白墙带红砖角石，三开间门廊上方为高山墙。模型只取甲楼在照片与航片中可以共同辨认的部分。[原图、来源与年代异文](../../../source/precise/xuhui-ailu-residence-garden-loggia/README.md) · [甲乙两栋的来源指纹](../../../source/precise/xuhui-ailu-residence-garden-loggia/reference-review.json)

原生场景重新打开后数得75组可编辑网格、20,788个三角面。网页远景为10,592面。三档各通过56条表面射线，检查券石、上部石栏的前后位置、廊内木窗及琥珀色半圆窗、西端雨篷、两个烟囱与外部空地。石料颜色、券高和屋顶进深由照片估算。[原生重新打开与材质核对](geometry-native.json) · [三档射线](surface-checks.json) · [原生渲染](xuhui-ailu-residence-garden-loggia-preview.png) · [与原照目检](visual-review.json)

地物3522与实取OSM足迹交并比98.73%。本件替换园侧敞廊、西侧窗和东翼的一段屋面。原来楼体近景保留49.06%，远景保留49.05%。近邻4306的两档网格分别与裁剪边界相距1.91米、2.01米。20个地面位置核验了花园、露台、门后房间、廊柱、东侧路面和甲楼后部。石柱和房间挡住行人，拱下至后排门窗之间保留通行空间。两个屏幕尺寸下，庭院门洞、栏杆、老虎窗及烟囱的7条视线均通过。[地块来源](../../../source/precise/xuhui-ailu-residence-garden-loggia/footprint-review.json) · [两档地物与地面](placement-geometry.json) · [桌面与手机视线](overview-sightlines.json)

[单体查看](../../../ailu-residence.html) · [原生工程及三个模型文件](../../../assets/models/candidates/xuhui-ailu-residence-garden-loggia/manifest.json)

## 独立查看与下载

在1250×820桌面和390×844手机上实际切换了近景与远景。四幅截图可辨中央宽券、上层石栏和西端较低的雨篷。原始GLB、网页近景、远景和Blender工程共2,495,787字节，四个保存文件的SHA-256均与清单一致。[浏览器操作及下载](viewer.json) · [手机近景](viewer-mobile-full.png) · [桌面近景](viewer-desktop-full.png)

## 城市目录与地面

加入甲楼后，城市目录由252处增加到253处。最终服务的1,532个输入文件全部通过实际HTTP下载，合计1,299,077,120字节。目录中保留甲、乙两栋的身份说明。桌面与手机已实测的独立页、加载程序和模型文件与最终服务逐一相同。[逐层文件回读](release-http-summary.json) · [地点卡与独立页核对](formal-26216-page-identity.json) · [四幅图与最终文件对应](formal-26216-viewer-http.json)

地面运行检查采用最终目录的实发字节，验证了庭院、敞廊、保留楼体及6处邻楼的26个点位；原有甲楼背面继续保留。该记录覆盖运行模块与碰撞边界。第216期在前后两代全城地图上实测了11幅画面。鼠标与触屏分别在地图上点中了甲楼灯牌，均由赛华公寓切换到甲楼。五个建筑机位拍到花园敞廊、临街券口、屋顶、石栏和老虎窗，远景核对了实际加载的两档模型。[11幅地图与逐图观察](final-map-31216/manual-visual-review.json) · [建筑取景与26个地面点位](final-map-31216/architecture/main-browser.json) · [四幅独立页及下载记录](final-map-31216/standalone-manual-visual-review.json)。[运行模块与地面点位](city-25216/runtime-placement.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/a6e50ca5545c9202bbac5589a6540a7fa28008d3/projects/shanghai/index.html#landmark=xuhui-ailu-residence-garden-loggia&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，11 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
