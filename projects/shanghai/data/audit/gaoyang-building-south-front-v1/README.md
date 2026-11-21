# 高阳大楼东大名路双塔正立面

本栋对应市级名录2F006、虹口区东大名路817号。南洋兄弟烟草公司办公楼的双塔、弧形塔窗与中段退进可从1937年两张资料和1949年的两张档案照片复核。近年正视照片可见两侧各四个街面长窗开间、中央窗组和柱廊。大楼的近年外观是本次建模依据，旧厂门、三层砖厂和办公室后段各自保留在来源记录。[名录、分期及原照](../../../source/precise/hongkou-gaoyang-building-south-front/README.md) · [独立查看](../../../gaoyang-building-south-front.html)

原始和网页近景均为67,592个三角面，远景31,300面。Blender重开检查取得236个可编辑网格。三个版本的独立射线分别检查129、129、121处，含窗格进深、券窗、门廊立柱、柱间通道、顶棚底面、塔亭窗、弧形罩及旗杆。原生工程首次重开时发现部分构件名称超过Blender的63字节限制，缩短后逐项比对网格、面数和材质。第一次渲染中，东端两面转折墙缺少实照可见的窗洞。最终两面各补上五层真实凹进的窗，并在三档模型中逐窗验证。[网格重开](geometry-native.json) · [原生图](hongkou-gaoyang-building-south-front-preview.png) · [射线逐项记录](surface-checks.json) · [转角修订与来源](corner-window-review/review.json) · [修前](corner-window-review/east-before.jpg) · [修后](corner-window-review/east-after.jpg)

源852比临街办公楼更深，后部保留旧底图。实解两档地块网格后，近景保留82.09%，远景保留82.20%，邻楼至裁区的净距至少7.77米。中央门廊仅16厘米高的铺地可行，四根柱础和门后主体阻挡。24个本栋地面点逐项复核，桌面和手机默认相机分别检查9处塔亭、翼窗、东端及中门特征。[实际近远源与探点](placement-geometry.json) · [落位合同](final-placement-contract.json) · [双端视线](overview-sightlines.json)

独立页已在桌面与390像素触屏分别拍下正面、斜视和俯视。正面可见临街两翼的拱窗与中间四柱；斜视可见东塔翼两列转角窗及中央退进。俯视显示双塔方座和中段平顶，树木遮蔽处的门廊底部与塔帽饰件仍是近似。两端均以实际控件切换，四件原始、网页、远景与Blender文件均已保存并核对。[桌面斜视](viewer-desktop-full-oblique.png) · [手机正面](viewer-mobile-full-front.png) · [六视图与范围](visual-review.json) · [下载与网页输入](viewer.json)

正式登记从261处增加至262处。原始父版的1,585项逐一复核，并从原服务和当前服务各获取同一地块的远、近几何。实际渲染程序在源852下新增两个裁切三角与一段封口，保留其他图层的裁切；全城共1,592个裁切三角，分布于22个宏图块，最大单表336个。30个地面点包含24个本栋探点及6栋邻楼，两套矢量源合计核对14条。27225版完整读取1,610项、1,336,625,697字节；单体页的1920年设计、1921年竣工、1937年和1949年影像说明也已与唯一地点卡核对。[城市运行记录](runtime-placement.json) · [父版近远原件](parent-224-source-bytes.json) · [逐层读取](city-27225-all-http.json) · [正式单体页与目录](city-27225-viewer-and-card.json)

28225版完整实取1,610项、1,336,627,242字节。东大名路817号这项的定位、四件模型、城市地点卡和三种屏宽的候选相机均已同前版比对。单体页中的区属、1920年设计、1921年竣工及档案照片年代也已在正式入口复核。[最终版区属、页名与四件下载](city-28225-viewer-and-card.json) · [两代候选位置与相机](city-28225-signed-inheritance.json) · [正式全站读取](city-28225-all-http.json)

## 普通地图入口与两端实拍

从前一版的261处地点切换至262处。手机从地点目录触屏选中并点击地图标牌，桌面从目录用鼠标选中，随后以键盘切换和返回。每次切换都核对模型、裁切范围和页面给出的地点名。[前一版同机位](city-31225/map-before.png) · [返回本楼](city-31225/map-returned.png)

下表按实际画面中各构件采样点的位置，统计位于画幅内且避开标牌和页面控件的点。单个点只代表该构件选定位置。

| 实拍 | 画幅 | 露出的采样点 |
| --- | --- | --- |
| [手机稳定画面](city-31225/map-mobile-same-camera.png) | 390×844 | 9/9 |
| [桌面稳定画面](city-31225/map-desktop-same-camera.png) | 900×650 | 9/9 |
| [手机公开加号](city-31225/map-mobile-public-zoom.png) | 390×844 | 6/9 |
| [细看立面](city-31225/map-street-facade.png) | 700×550 | 7/9 |
| [屋面](city-31225/map-roof.png) | 700×550 | 6/9 |

浏览器分别签收近景与远景模型，核对原有近、远底图，并实取四份文件。公开站整读1,610个文件，地面通行及周围楼房合计30个采样。对照、手机、桌面、键盘切走并返回、街面与屋面、远景六个独立会话均已结束，退出码均为0。[远档](city-31225/map-distant.png) · [各视图与遮挡位置](city-31225/default-screen-coverage.json) · [完整签收](city-31225/result.json)

[单体与下载页](../../../gaoyang-building-south-front.html) · [原始GLB](../../../assets/models/candidates/hongkou-gaoyang-building-south-front/hongkou-gaoyang-building-south-front-raw.glb) · [网页近景GLB](../../../assets/models/candidates/hongkou-gaoyang-building-south-front/hongkou-gaoyang-building-south-front-web.glb) · [远景GLB](../../../assets/models/candidates/hongkou-gaoyang-building-south-front/hongkou-gaoyang-building-south-front-lod.glb) · [Blender工程](../../../assets/models/candidates/hongkou-gaoyang-building-south-front/hongkou-gaoyang-building-south-front.blend)


长屏手机与宽屏桌面的初始正面可以辨出高阳大楼两端的塔冠、上层连续窗和下层门前廊。临街专项图能辨塔身与两列弧窗。南门廊近摄、键盘回返和小视口远景中，打开的详情卡盖住下半幅；这三张各有九处采样点被控件遮住或落在画幅外。屋面和塔冠两张从较高机位还能分别看清六处和五处采样点。独立页正面保留两座迭层塔冠、完整底层入口和中间廊柱，俯视能辨两端屋顶之间的高差。 [十二幅城区与六幅单体实拍的逐图复核](city-31225/manual-visual-review.json) · [单体正面](city-31225/standalone/viewer-desktop-full-front.png)

正式31225单体页面在桌面与手机分别实拍正立面、斜侧和远档俯视，六张图均保留原始像素与散列。四个下载按钮实际保存原始、近景、远景及可编辑工程，下载字节与模型清单逐件吻合。[六张实拍与四件下载](city-31225/standalone/viewer.json) · [两代城区与相机](city-31225-signed-inheritance.json) · [六个地图会话的退出凭据](city-31225/225-map-slot-released.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/67167d8cd279f0feaf8056594cbf341280961dea/projects/shanghai/index.html#landmark=hongkou-gaoyang-building-south-front&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
