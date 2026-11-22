# 三井洋行四川中路东立面南端山花与入口

2013年12月19日的街照与1908年出版的图版能辨认同一组红砖墙、交替石隅、双洞、三连拱和三角山花。沿四川中路向北紧邻的石门罩旁，绿色门牌写181。市房管局2A055登记门牌185，工作名录采用175；照片中的175同时是街区路牌的南端号码。[原片、年代与门牌](../../../source/precise/huangpu-mitsui-bussan-pediment-front/README.md) · [街照局部及署名](photo-credits.md)

模型留出真实的窗洞和拱形窗头，玻璃与木框坐在砖墙后方。三角山花、三根底层石柱、上层连拱柱、石门罩、小门牌与檐口短齿分别成形。原始和网页近景各17,196个三角面，远景6,236个。三个GLB各用49条射线检查窗、柱间、山花、门牌和屋顶截面，四件都含相同的原创红砖纹理。Blender原件保留可编辑网格、砖面UV和内嵌原图。[逐档射线](surface-checks.json) · [原生几何](geometry-native.json) · [四件砖面纹理](brick-texture-four-files.json) · [原生渲染](huangpu-mitsui-bussan-pediment-front-preview.png)

桌面与390像素触屏各打开正视近景、斜视、简化远景，浏览器完成原始GLB、网页近景、远景和Blender工程四次下载。手机能分清双洞、三连拱、山花及门罩，浅石饰和181号小字在默认远景较小。门扇、被电线遮挡处与背侧截面按照片比例估计。[六张实图与四次下载](viewer.json) · [桌面斜视](viewer-desktop-pediment-and-number-181.png) · [手机远景](viewer-mobile-lod.png) · [图像比照](visual-review.json)

具名的OSM 380339927号足印与城市2085号原楼重合98.29%。本件取东立面南端约11.5米，街墙正面向东偏北约74.3度。近景原屋保留656.12平方米，远景保留648.67平方米。旧矢量中与这段立面相交的是2927187770号的第56块，周围17个分件均保持原样。两条街的路面和相邻四栋均在裁切外。桌面与手机的默认相机分别对八个实体构件核过视线。[原楼与道路](../../../source/precise/huangpu-mitsui-bussan-pediment-front/footprint-review.json) · [成品几何、原楼与地面](placement-geometry.json) · [默认视线](overview-sightlines.json)

登记前又用真实近、远景网格和周围原有楼栋比较了九种机位。选定朝向263度、俯角30度后，870像素桌面、390像素手机及1280像素宽屏的近远两档都能完整看到模型投影，八个观察点全可见。[几何投影实算](pre-registration-framing.json)

第234期冻结的271处目录中无人占用2085号原楼。现有最近的精建轮廓为相距17.07米的新汇丰大楼（汇丰银行职员宿舍）；九江路50号原三井银行使用另一地块。加入本期后，真实前版矢量的17个其他要素未发生变化。[原楼、库存与邻屋](final-prior-coverage.json) · [真正前版矢量对照](vector-on-predecessor.json)

三井洋行作为第272处新增地点，逐项复核了前版1,665个签入文件和本版1,673个签入文件。 正式末层31235逐一下载了1,690项，共1,382,885,217字节。 在28234、28235和31234、31235上重新读取了来源图块与原楼轮廓，新版还重新下载了两档展示模型、原始网格和可编辑源文件。[逐层签收清单](signed-stations/final-bound-stations.json) · [正式前后两版的模型与原楼](signed-stations/real-31k-predecessor-and-new-building.json)

[正式地图与单体页的脚本、样式及分段请求核对](formal-31235-runtime/README.md)

## 正式城市地图复核

桌面鼠标和手机触屏均从地图点进四川中路的三井洋行，十四个地面和邻屋测试点都与原城预期相符。沿街初始机位被前排屋顶遮挡。按立面测绘重新取景后，红砖外墙、三联拱窗、浅色山花、右侧入口和相邻屋顶可以同看。门口近景保留了绿色「181」门牌和石门罩。远景已切换到远档模型。[沿街立面与相邻屋顶](city-31235/actual-readable-frontage/frontage-and-retained-roof.png) · [三联拱窗与山花](city-31235/actual-readable-frontage/three-arches-stone-pediment.png) · [181号入口](city-31235/actual-readable-frontage/entrance-181-and-stone-surround.png)

在本期独立模型页以 1250 和 390 像素宽的视口分别检查了正面、斜面和远档。两侧均可辨认红砖与浅色石饰的边界。原始模型、网页模型、远档模型和可编辑文件均通过浏览器保存，四份文件的字节和摘要与正式清单一致。[六张实图与四次保存](city-31235/standalone-31235/viewer.json) · [恢复经过与分场实录](city-31235/actual-current-and-recovery.json)

[实机、地面与四种下载](city-31235/process-exits.json) · [旧城对照](city-31235/map-before.png) · [四川中路南端山花与入口](city-31235/map-east-pediment-and-stone-doorcase.png) · [181号门牌与石门罩](city-31235/map-181-number-and-doorcase.png) · [远档](city-31235/map-distant.png)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/d68420a29d3f34e95a4eac11c988ef1496116b11/projects/shanghai/index.html#landmark=huangpu-mitsui-bussan-pediment-front&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
