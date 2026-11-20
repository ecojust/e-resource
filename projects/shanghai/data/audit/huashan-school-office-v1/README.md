# 华山路原美国学校办公楼

市房管局第二批名录2B019列华山路643号、639号。2018年照片记录639号门牌和院内临街的红瓦门斗，2024年市政府报道将643号院内的原学校办公楼列为约3165平方米的保护建筑。院西侧的马兰花剧场另有独立地块。衡山路10号的美童公学主楼另列徐汇区2D020。[名录、现场照片与建筑身份](../../../source/precise/jingan-huashan-american-school-office/README.md) · [照片方向与日期](../../../source/precise/jingan-huashan-american-school-office/reference-review.json)

模型覆盖临街拱门和草坪面两层柱廊。近景保留门玻璃、覆瓦门斗、上下层窗格、细铁栏、弧形转角与三组阁窗。高度、侧墙、露台曲率与部分开窗间距根据照片和2018、2022、2024三期航片估算。现有室内和园中舞台未建模。[三期航片与本地轴](../../../source/precise/jingan-huashan-american-school-office/roof-registration.json) · [原生预览](jingan-huashan-american-school-office-preview.png) · [与现场照片核对](native-visual-review.json)

原始与网页近景各有44,836个三角面，远景20,104面。可编辑Blender工程包含47个网格。三个版本分别完成54项材质和距离检查，包括门斗、后退的门玻璃、分格窗、廊柱、地坪和转角。近景上层窗的横档对应远景简化后的玻璃。[重建源程序](../../../source/precise/jingan-huashan-american-school-office/source/build_model.py) · [三档射线检查](surface-probes.json) · [可编辑网格](geometry-native.json) · [原生取景](native-camera.json)

14-13718-6695原生建筑3170的粗模型高22.9米，投影不能完整覆盖历史露台与门斗。按三期影像定位后的实际模型最高约11.98米。替换范围同时容纳原始屋面与重建后的投影，近、远两档与同组另外13栋的原网格分别保留6.56、6.63米的最小间隙。廊内、两柱间及门拱下的铺地可以穿行，实墙和方柱仍有碰撞。[实际网格、街面与通廊实测](placement-geometry.json) · [登记地块](final-placement-contract.json)

另一底图把办公楼与剧场合并进同一组2426个组成面。按既有169处登记建立旧态，仅去除办公楼约455.79平方米的组成面。邻接剧场在前后两次计算中均为329.71平方米，组内其余组成面的意外变化面积为零。[公开底图实际裁切](vector-source-checks.json) · [登记前169处地块核对](existing-map-coverage-169.json)

正式170处网页与169处前态按公开路径再次读取。新页面、导入模块、登记目录、资源清单与原始、网页、远景、Blender四种下载均已核对文件内容。[前后入口与四件下载实读](public-entry-bytes.json)

登记后的单体页面已在1250×820和390×844实测，两个视口均成功切换完整近景和简化远景，桌面实际下载的原始、网页、远景及Blender四件逐项通过文件名、大小与SHA-256核对。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [浏览器与下载数据](viewer.json)

## 正式主地图和通行复查

169处地图在花园一侧仍绘制旧办公楼的粗模型。170处地图的同一机位能看见完整的两层柱廊、弧角与三组阁窗。街面反向视图可见红瓦门斗和拱门。缩远至15.5级时，实际加载的模型从44,836面切换为20,104面。前后两代现场均使用同一个14栋近景组，新增的37个裁剪三角面只作用于源3170。同组剧场3433和其余12栋沿用原几何。[169处原图](city-24132/map-before.png) · [170处花园面](city-24132/map-street-facade.png) · [街门和屋面](city-24132/map-roof.png) · [远景](city-24132/map-distant.png) · [完整场景与输入记录](city-24132/main-browser.json)

首次从目录点入时，桌面和手机均曾在新模型已载入、原生近景瓦片仍未更新的阶段显示遮挡主体的浅色体块。没有缩放或旋转，在同一默认相机等待原生建筑和矢量裁剪就绪后，双端均显示草坪面的完整楼体。[原始手机首帧](city-24132/map-mobile.png) · [原始桌面首帧](city-24132/map-desktop.png) · [手机加载完成](city-24132/mobile-default-warm.png) · [桌面加载完成](city-24132/desktop-default-warm.png) · [相机、灯牌与加载状态](city-24132/warm-browser.json)

现场检查了8处办公楼及院地样点和13栋邻楼。廊下、柱间、门斗、草坪和入口通路均可通过，方柱、室内墙体及各邻楼继续阻挡通行。另外沿院廊与门斗各取21个连续位置，42个位置均可通过。实际运行调用建筑碰撞查询。两档模型和原生地块文件的下载均通过SHA-256核对。[21个定点与两条连续路径](city-24132/main-browser.json) · [两个矢量底图及近景组](city-24132/runtime-placement.json)

前态逐件核对827个冻结输入，新态核对835个。重新读取两代真实页面观察到的HTTP资源，前态共114件、59,634,166字节，新态共126件、85,677,894字节。独立查看器及四件模型的13项依赖在先前实际查看的版本和本次正式版本中逐件相同，沿用既有4张双端近远景截图。[前后发布版本](city-24132/release-bindings.json) · [前态网络资源](city-24132/http-131.json) · [新态网络资源](city-24132/http-132.json) · [独立查看器逐件比较](independent-viewer-24132.json)

完整读取了正式测试站的835项输入，共781,636,377字节。生成器也独立生成了相同的170处城市目录。[完整HTTP记录](city-24132/132-all-http.json) · [目录复算](city-24132/132-generator.json)
