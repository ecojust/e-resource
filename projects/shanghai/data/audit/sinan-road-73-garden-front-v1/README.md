# 思南路73号周公馆庭院立面

站在花园一侧，底层浅拱通向内部门扇，其上是两排深红木窗与栏杆。两翼后退，西翼可见石阶、铁扶手和百叶。窗格、栏杆、阶梯与拱下空间按2010年正面照片独立绘制，屋脊交线参考2020年斜照。原门牌107号与现址73号的对应见上海地方志。[照片、史料和制作范围](../../../source/precise/huangpu-sinan-road-73-garden-front/README.md)

Blender重新打开后比对了48个网格和13种材质。原始及网页近景各50,912面，远景5,492面。每档89条射线核对檐下、浅拱、后退内门、两层窗框、栏杆间隙、西翼百叶与坡顶。部分栏杆缝后可见木窗竖框，其余可透见玻璃。近景把每行瓦的端缝错开，远景保留坡面和逐行搭边。[原生渲染](huangpu-sinan-road-73-garden-front-preview.png) · [源文件与校验](geometry-native.json) · [267项实际射线](surface-checks.json)

底图4896原有楼体估高18.30米。现在庭院侧约13.74米宽，烟囱顶约13.40米，底层仅在前2.65米局部替换。后段旧墙在8.09米檐线以下保留，近景与远景保留的地面投影分别为82.6%、82.9%。旧楼背段上方的高度裁切只针对4896。从邻楼实测网格到裁切范围的最小水平间隔为6.89米。浅拱下可走到内门前，西翼石阶上的扶手与台面各有地面探点。[真实源网格及探点](placement-geometry.json) · [落位与高度范围](final-placement-contract.json) · [桌面与手机视角测算](../../../source/precise/huangpu-sinan-road-73-garden-front/camera-preflight.json)

201处和202处正式站点的前161条增补目录一致。裁切仅在原楼4896的图块中加入4个三角形，其中2个限定檐口以上的高度。两套矢量源共核对18条结果，另检查29处地面与邻楼。新版本逐项实取1,113个HTTP文件，共1,016,555,610字节。[实站相邻版本](renderer-parent-controls.json) · [运行时矢量与地面](runtime-placement.json) · [实际下载清单](renderer-release-http.json)

独立页在桌面及390像素手机上均可切换近、远景，并可下载原始、近景、远景和原生模型。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [四件下载](viewer.json)

初版原生图的屋坡只有横向瓦行，近景现按行错开瓦的端缝。手机正视图仍可辨两层窗廊与底部通道。[初版与修订渲染](roof-detail-review/inspection.json)

## 市区地图上的庭院立面

从31164的201处地点到31165的202处，新入口位于思南路73号周公馆庭院侧。手机目录点选、手机放大、桌面鼠标和离开后返回，都能找到底层浅拱、上下两排深红窗廊及西侧阶梯。原街面近景右半部被实际保留的邻楼挡住，移至庭院一侧后，两排木格窗、栏杆、拱脚和西阶可以一起辨认；屋面图显示红瓦坡面及屋脊交线。模型只覆盖已核实的庭院立面，后段屋体仍按原城市地物显示。[原街面机位](city-31165/map-street-facade.png) [庭院近侧](city-31165/map-garden-court-side.png) [手机目录](city-31165/map-mobile.png) [桌面目录](city-31165/map-desktop.png) [红瓦屋面](city-31165/map-roof.png)

核验保留了1张前态和10张后态城景，检查4个局部裁片、1个切面及29个地面样点，其中包括8栋邻屋。第一次前态读取相邻分区远景时收到HTTP 502，补齐相同签名的原始文件后，正式前态重新通过。第一次后态完成9张图及29个地面点后，渲染进程在远景切换时退出。另开同一正式站目录，再次加载近景，切换远景并核实六项实际下载，最终进程正常退出。31165全部1,118项文件共1,016,606,490字节逐件匹配签名。[前态](city-31165/control-browser.json) [后态及两段记录](city-31165/main-browser.json) [最初的前态错误](city-31165/first-control-native-far-502.json) [首次后态退出](city-31165/main-before-renderer-crash.json) [远景复验](city-31165/distant-fresh-browser.json) [完整HTTP收据](city-31165/165-all-http.json)

模型文件可直接下载。三档GLB与可编辑Blender分别在独立页和城市入口逐字节核对。[原始GLB](../../../assets/models/candidates/huangpu-sinan-road-73-garden-front/huangpu-sinan-road-73-garden-front-raw.glb) [网页近景](../../../assets/models/candidates/huangpu-sinan-road-73-garden-front/huangpu-sinan-road-73-garden-front-web.glb) [网页远景](../../../assets/models/candidates/huangpu-sinan-road-73-garden-front/huangpu-sinan-road-73-garden-front-lod.glb) [可编辑Blender](../../../assets/models/candidates/huangpu-sinan-road-73-garden-front/huangpu-sinan-road-73-garden-front.blend)
