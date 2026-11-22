# 滇池路120号业广地产公司大楼街角

[独立模型](../../../dianchi-land-investment-corner.html) · [地图位置](../../../index.html#landmark=huangpu-dianchi-land-investment-corner&mode=overview) · [街照和登记](../../../source/precise/huangpu-dianchi-land-investment-corner/reference-review.json)

2015年公开的街角照片给出了斜切角、两侧各一跨、阁窗与两面山花、三侧连通的二层阳台。核对影像时采用市房管局2A016以及滇池路120号足印。滇池路100至110号的仁记洋行为相邻独立建筑。两条街的其余墙面与完整屋顶留待补证。

近景模型有11,552个三角面，远景模型有7,276个。原始GLB、近景和远景按实际解码后的表面各做36处射线检查，覆盖玻璃、石窗头、砖面、楼层檐线及阳台栏杆。原始贴图为本模型生成的1024像素顺砖纹理。[三档表面](surface-checks.json) · [可编辑原件与制作参数](geometry-native.json)

替换区域为44.05平方米。近景原街区网格中有1582个三角面碰到该区域，远景有18个，归属均为本楼3157。按有明确归属的远景足印计算，保留面积为94.96%。地面检查包含27处，周围14座建筑均保持原形，普通桌面和手机相机均能看到8个选定构件。[原街区裁切](source-cut.json) · [地面与邻屋](placement-geometry.json) · [相机视线](camera-sightlines.json)

四件文件均内嵌同一张原创的1024 × 1024红砖贴图。三个GLB的红砖材质均引用实际纹理坐标，Blender 文件包含原始55,579字节PNG及对应的材质节点、UV图层。[逐件纹理核对](packed-masonry.json) · [复核脚本](check-packed-masonry.py)

## 城市底图与独立模型页

从实际源站逐件读取1,714项，共1,399,361,737字节，对照来源清单逐项核对SHA-256。地图目录从274处增至275处。仁记洋行原有4片裁切保留，业广街角新添8片。两套矢量底图分别保留同一业主的后部楼体。先前的采样只覆盖沿街一侧，在补入后楼内部的原始地面点后，42处地面与30项矢量检查均通过。[全部文件](31238-all-http.json) · [两版实际目录](final-renderer-31238-http.json) · [地面、矢量与裁切](runtime-placement.json) · [补充采样记录](retained-ground-review.json)

1250像素桌面与390像素手机实拍近景和远景。两侧券窗山花、平顶阁窗及连通的二层阳台均保持辨识；手机远景上细铁栏较小。可编辑Blender与三份GLB均通过实际下载与SHA-256核验。[桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [四款下载及视图记录](viewer.json)

### 街角的两次地图点选与八幅独立视图

在含275处地点的地图中，鼠标和触屏分别从仁记洋行点到业广地产公司大楼，登记的业主为3157号。街面、屋顶、两侧山花与阳台分别拍摄，42个地面样点逐点比对。拉远后地图把此楼并入一个含16处地点的图钉组，当时载入的远景网格为7,276面。[街角图](city-31238/map-street-facade.png) · [两侧山花](city-31238/map-sichuan-and-dianchi-gables.png) · [远景](city-31238/map-distant.png) · [两次点选与地面记录](city-31238/main-browser.json)

独立模型页在1250像素桌面和390像素手机上各留四幅图，可对照斜切角的两侧宽度、转折的阳台、山花与保留的屋顶截面。原始GLB、网页GLB、远景GLB与Blender文件都由页面下载按钮另存并逐件核对摘要。[桌面斜视](city-31238/standalone/viewer-desktop-full-oblique.png) · [手机俯视](city-31238/standalone/viewer-mobile-lod-above.png) · [视图与保存记录](city-31238/standalone/viewer.json) · [18幅图的逐张意见](city-31238/visual-review.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/e7c760a57cb5d4b9cd0a4716b074a7127a5fb954/projects/shanghai/index.html#landmark=huangpu-dianchi-land-investment-corner&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
