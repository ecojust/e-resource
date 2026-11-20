# 广学大楼西立面核验

首轮原生渲染与虎丘路实景对比后，调高了石尖拱的弓高，补出两翼超过女儿墙的浅色柱头和各间双尖饰。最终渲染来自重新打开的Blender 4.3.2工程，使用48次Cycles采样和Open Image Denoise。69个网格可以独立编辑。原始及网页近景均为163,542个三角面，远景为84,746个，均有18种材质。[初版](preflight/first-native.png) · [最终渲染](huangpu-christian-literature-building-preview.png) · [解码与原生校验](geometry-native.json)

对近景、原始和远景各执行65项检查。逐间取样核实窗、折面柱、连续石框、门洞退深及装饰板。另对上下两行凸字的三角面进行分层计数。[195项检查](street-checks.json) · [复算脚本](check-street.py) · [照片与修缮年代](../../../source/precise/huangpu-christian-literature-building/reference-review.json)

虎丘路沿街面来自西楼3051。仅前2.87米参与裁切，远景原体保留85.63%，近景按共同后墙归属的不确定性得85.36%至85.46%。2015年照片和2022年报道可辨中央尖拱为西楼。以东邻2954为可能归属的全部近景三角面至裁切边界至少15.58米，远景18.93米；其他建筑被移走面积为零。三版GLB在距地1.15米处测得主门扇距街面0.55米、门玻璃0.464米、拉手0.3775米、两侧窄洞的门扇0.61米；据此分别留出凹口。13个地面点核实门前铺装、凹处、实体门面、保留的后半栋和东邻。[两楼地块与原生输入](../../../source/precise/huangpu-christian-literature-building/footprint-review.json) · [近远原体及地面取样](placement-geometry.json) · [地图参数](final-placement-contract.json)

视角按两侧街屋实际高度复核。在88°朝向、37°俯角下，桌面及手机的街口和上层窗点均能从对街屋顶上方看到。计算取样捕捉的是自身可见的7,523个正面候选点，后续城市页面截图单独记录。[逐视角射线](street-camera-comparison.json)

139处冻结城市站通过533项HTTP文件核对，共414,401,309字节。实际运行时西楼3051在同一近景组使用两片裁切，东侧真光大楼2954和组内其他独立建筑保持原状。保留的东楼和西楼门前分别核对了地面位置。[网络收据](frozen-http.json) · [运行时几何和地面核验](runtime-placement.json)

正式139处站点在1250×820桌面及390×844手机上打开了单体页。近景163,542面、远景84,746面，中央尖拱纳入两种视框，底层入口、砖色竖带和横向窗列可见。页面四件实际下载均通过字节校验，核对时未记录页面异常。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机远景](viewer-mobile-lod.png) · [浏览器收据](viewer.json)

138处前态的真实主图在虎丘路同址显示3051号西楼的原底图外观。此次相机还保留了相邻光陆大楼，2954等独立楼体经原主图读取。前态目录为06dd0e47开头，11项HTTP核对通过，浏览器未记录页面或请求错误。[同址原楼](final-map/map-before.png) · [138处前态报告](final-map/control-browser.json)

139处主图在390×844手机上从目录点选广学大楼，桌面重新打开同一条目。两端均显示163,542面近景，中央尖拱、两翼窗列和底层门口可辨。沿街视角可同时看到光陆大楼，俯视可辨虎丘路外墙与保留主体的接合处。拉远至15.5级实际换用84,746面远景。17个地面点覆盖门前退进、保留后墙和四个邻楼。四件模型、两份城市源文件及八个运行文件的实际响应分别核对通过，浏览器未记录异常。[手机](final-map/map-mobile.png) · [桌面](final-map/map-desktop.png) · [沿街](final-map/map-street-facade.png) · [屋面](final-map/map-roof.png) · [远景](final-map/map-distant.png) · [139处主图报告](final-map/main-browser.json) · [发布输入与四件文件](final-map/served-inputs-139.json)

从139处版本起，默认灯牌布局会为当前选中的外立面留出显示空间。[灯牌可见性对照](../selected-facade-labels-v1/README.md)
