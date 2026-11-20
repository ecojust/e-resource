# 怡和洋行大楼临江立面与北京东路转角

模型覆盖中山东一路27号面向外滩的九个开间，向北延伸至北京东路斜角。中央双门、石券分块、四根跨层圆柱及石栏杆来自现状和历史照片。檐上的两排窗、阶梯式石屏与旗杆按2014及2025年影像复原。1920至1922年建成的主体与早期同址建筑有别，加层年代的不同记载 见来源档案。[研究记录](../../../source/precise/huangpu-jardine-matheson-building/reference-review.json) · [单体三维预览](../../../jardine-matheson.html) · [原址主图](../../../index.html#landmark=huangpu-jardine-matheson-building&mode=overview)

## 几何与交付文件

沿成品模型的九扇拱窗、券顶、四根圆柱、中央双门及壁灯逐点射线抽查。三档模型的各31个抽样点均命中预期材质与深度，街侧净空也已核对。[几何抽查](surface-probes.json)

原始和网页网格各33,332个三角面，远景20,672个。两份压缩网格经逐材质解码，定向三角面与各自原始网格一致。Blender 4.3.2 重新打开77个可编辑网格，逐材质表面与原始GLB匹配，原生文件保留朝向外滩和东北斜角的居中相机。[网格与原生核验](geometry-native.json) · [重开后的完整画面](huangpu-jardine-matheson-building-preview.png)

| 文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| 原始 GLB | 1960400 | `9dbb3cc068bfb51477008eb7ff8154b3a3ef8bfbb35fbb44dad0d7a542f45918` |
| 网页 GLB | 727656 | `db3b0cfe5a65c4d51d7521f3010b9649f91c6089760266dd335f955955425acf` |
| 远景 GLB | 427592 | `a8c1ca4f41506132b85b721329db9b6a87ca5c6a4befd79c515c1e1f08162267` |
| Blender | 548896 | `24bd19519df4535e2a551674152d85b5f00c46ba0973c2f830b224a758e8f087` |

## 配准与浏览验证

近、远景分别解码现状地块的GLB。模型占833号独立建筑东侧约11米，两个精度均保留原地块约73%的投影，区域覆盖其西翼和凹院边界。近景同一网格内另外四幢建筑与裁切零重叠。贴近地面的模型投影形成约576平方米碰撞区。截面按原市块22.4米屋面和实际相交线段封口，街道保留通行。正面水平尺度和方位按已登记地图长边确定；石作、柱头、层高和截深按照片比例估计。[配准合同](final-placement-contract.json) · [真实城市网格证据](footprint-review.json) · [源面与邻体](../../../source/precise/huangpu-jardine-matheson-building/footprint-review.json)

已在桌面1250×820和手机390×844核对单体页，包括两档模型和四份下载。已实测登记前99处的原城市视图，以及100处目录在手机中选中怡和洋行、显示模型与街道的过程。320×568窄屏中实测100枚灯牌无重叠，触摸第100枚后载入完整怡和洋行模型。该三位数实测有18×8像素字墨，左右各留4像素。桌面街面、屋顶和远景均通过，地图分别载入近景与远景模型。九处碰撞检查覆盖模型、保留的西部楼体、开敞凹院、外滩步道、北京东路及四栋附近建筑。首次桌面直达因城市目录25秒超时，曾回退到普通底图；后续从正常区目录进入后成功取得精细瓦片。[三位数实触](compact-browser.json) · [320像素全屏](map-100-markers.png) · [首次底图回退](desktop-fallback-observation.json) · [99处街景对照](control-browser.json) · [100处手机目录与主图](mobile-browser.json) · [单体页浏览器记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png)

正式桌面记录绑定四份交付资产及原城市远、近景瓦片的真实响应。手机从区目录实触地点的记录独立保留。街面和屋顶视角都显示同一833号建筑的单段封口；近景网格另外四个来源保持原样。[桌面、地面与资产逐项核验](main-browser.json) · [街面](map-street-facade.png) · [屋顶](map-roof.png) · [远景](map-distant.png)

灯牌布局、目录及取景回归共 43 项通过。目录核验现会沿带版本号的单体预览模块检查下载实现，并逐项检查四种资产的路径、大小与哈希。[回归记录](directory-regression.json)
