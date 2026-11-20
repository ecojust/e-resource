# 愚谷村愚园路北弄门核验

可编辑场景在Blender 4.3.2重新打开后，核对了34个网格、10种材质和20,688个三角面。网页远景模型有15,688面。[重新打开的原生预览](jingan-yugu-village-north-gate-preview.png) · [模型与来源校验](geometry-native.json)

逐一向两块三字名牌、绿色门牌、金属底牌、门柱、门轴和四格铁门投射射线，各档97处，共291处。门栅间留出了能看通的空隙。[首个可见表面测试](surface-checks.json)

四个底图近景组和整块远景的最近间隔为3.63米。保留相邻的五个底图建筑，只在石柱、两翼与闭合门扇处设置碰撞。18个站位和150次使用实际步行控制器的接近测试均已通过。[底图与地面](placement-geometry.json) · [步行测试](closed-leaves-walk.json)

对街底图建筑会挡住径直朝门看的42°视角。默认相机沿愚园路略微转向，桌面和390像素手机可看见两块竖牌和四格铁门。[相机视线](camera-preflight.json) · [来源与估计范围](../../../source/precise/jingan-yugu-village-north-gate/README.md)

实际独立页在桌面和390像素手机切换近远模型，并逐个下载四件文件。铭牌和门扇在两屏都可辨，深色栏杆在灰底原生预览中更清楚。[网页与下载收据](viewer.json) · [四幅实图目检](visual-review.json)

最终渲染器的前后城市目录都含988个裁切三角面。本次加入独立门头后，四个临近网格组以及五栋邻楼在两个矢量源中的处理结果一致。[运行时对照](runtime-overlay.json) · [固定资源核验](renderer-release-http.json)

## 正式地图与用户操作

在正式186处与187处两张地图上实测同一弄口。增加门楼后，桌面和手机均可点选，门前街道、门后弄道以及五栋邻楼保持原有边界。[六幅地图和通行核验](city-24150/README.md) · [门柱、竖额和四扇铁门](city-24150/map-two-name-tablets-and-closed-leaves.png)
