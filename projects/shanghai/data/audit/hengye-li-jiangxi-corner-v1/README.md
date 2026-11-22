# 恒业里江西中路115号泗泾路转角

上海市房管局将恒业里列入第三批优秀历史建筑，名录编号3A015。本次制作江西中路115号与泗泾路交会处的三层街墙。2014年照片中的115门牌用于定位。2019年与2021年的街景都能看到底层圆角砌实、泗泾路一侧浅券窗和江西中路一侧方口。保留两街其余门牌段及135弄各宅。[照片与名录](../../../source/precise/huangpu-hengye-li-jiangxi-corner/README.md) · [独立浏览与四件下载](../../../hengye-li-jiangxi-corner.html)

近景13,952个三角面，远景7,836个。重新打开Blender后逐一比对40个可编辑网格及材质，并核验两张原创砖纹及贴图坐标。原始、近景与远景各测76条射线，覆盖窗框、凹玻璃、腰线、弧面与檐口。独立页以桌面鼠标、390像素触屏各拍三图，并核对四次实际下载。[原生与网格](geometry-native.json) · [三档贴图与Blender内嵌砖纹](brick-texture-checks.json) · [228条射线](surface-checks.json) · [独立页六图及下载](viewer.json) · [进程退出](native-and-viewer-exits.json)

城市底图的2354号建筑沿两街形成直角。新模型将照片可见的转角做圆，保留近景原始投影97.54%和远景97.65%。底图楼后高19.2米，临街三层檐口约11.5米，按照片估计。检查街角圆弧处的人行余地、门外浅台口、砖墙和后部原体量共28个地面点，另核对包括135弄住宅在内的18处邻屋。五段切面在近、远两版间的最大平面距离为0.076米。[同机位增量对照](original-and-proposed-corner.jpg) · [近远底图与地面](placement-geometry.json) · [地图参数](final-placement-contract.json)

矢量底图将本楼合在高22米的85部件建筑对象38987380内。只裁去街角22.49平方米，另外84个部件与三个相邻对象均保持原有覆盖。普通目录机位朝向-58°、俯仰38°，桌面与手机各复核12条视线，四周共纳入459个底图体量。[矢量变化](initial-vector-comparison.json) · [相机与邻屋](overview-sightlines.json)

另从31253正式服务逐件读取独立页、浏览模块及其全部依赖、样式、清单和四个下载，与桌面和手机实拍会话的输入校对散列。[正式服务与双端会话的文件对应](standalone-31253-bindings.json)

普通城市目录由287处增至288处。地图核验了江西中路与泗泾路转角的五处墙体切面、28个街角地面点和18处邻屋。两次浏览器在相同位置拍摄街角，第二幅收起了资料卡，可见深砖圆角、红色横带和浅色挑窗台。金色地标提示仍遮住中央一小部分。两次窗口均已退出。第一轮在拍完画面后发生崩溃，留存了原图和进程记录。[普通城市中的十幅图与独立页六幅](city-31253/visual-review.json) · [原有界面](city-31253/supplemental-corner/first-attempt/street-corner-with-controls.png) · [同机位的街角实景](city-31253/supplemental-corner/completed/street-corner-map.png)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/815da679e9499ff9295f91893af5f310a9ba8145/projects/shanghai/index.html#landmark=huangpu-hengye-li-jiangxi-corner&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
