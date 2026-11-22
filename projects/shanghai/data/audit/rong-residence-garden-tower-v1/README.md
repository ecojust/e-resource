# 荣氏花园住宅角塔与首间柱廊的外观核验

从街角看，底层拱窗以上还有两层矩形窗。窗面随塔身折转，窗台下的花环也分布在不同朝向。转到花园一侧，可以从柱与后墙之间看到通道，斜看二楼时，黑铁栏的圆环轮廓与后方门扇重叠。近景的窗下花环可分辨两端垂带和逐片搭接的叶子；远景保留垂带和下垂的弧线。两档各用十个相同机位检查，两个全景都从地面覆盖到顶端尖饰。[街角全景](preflight/full-views/from-the-street-corner.jpg) · [窗台下的花饰](preflight/full-views/festoon-under-the-sash.jpg) · [廊内横看](preflight/full-views/along-the-veranda.jpg) · [远景的同一花饰](preflight/lod-views/festoon-under-the-sash.jpg)

圆顶的面板在相邻板带错开，颜色取红褐色，折角的立墙用浅灰米色抹灰。两张纹理由独立程序生成，进入未压缩、近景与远景网格后都逐字比对，并按实际面的顶点检查了纹理坐标。近景31,248个三角形，远景16,754个。源网格的516个部件按名称归入115个可编辑组。[屋面近看](preflight/full-views/roof-balusters-and-copper-seams.jpg) · [逐材质纹理检查](preflight/surface-textures-and-editable-groups.json) · [可编辑组和部件](preflight/editable-geometry.json)

每档网格用84条射线检查。74条应先碰到指定的窗、拱心石、花饰、屋面或廊柱材料，10条应穿过上下两层柱廊与屋面石栏之间的空处。每条记录均列出起点、方向和实际首个交点。建筑的绝对尺度取自照片拟合；中央窗面宽3.30米和首道腰线高4.50米为估值。[三档实物检查](preflight/geometry-rays.json) · [两张照片的逐点拟合](../../../source/precise/jingan-rong-residence-garden-tower/measurements/two-photo-fit.json)

地图只替换原城住宅西南端的角塔和相邻首间柱廊。近远两份底网都保留了原住宅约84.7%的投影面积。桌面和手机的普通目录视角各查12处，再从同一眼位检验模型表面实际最先碰到的材料。航照和地面照片给出的院内定位误差约4米。[地图定位与原屋保留范围](placement-notes.md) · [二种屏幕、二档网格的首个交点](preflight/garden-model-camera.json)
