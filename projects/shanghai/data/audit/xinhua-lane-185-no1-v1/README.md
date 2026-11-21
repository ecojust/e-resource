# 新华路185弄1号花园住宅核验

第三次普查的窗墙封闭了底层廊道，2024年修缮后第四次普查原照中可见三道敞开的浅尖券。实景俯拍中可见一栋低侧翼和前院另一栋独立房屋。市府英文导览的前两张图分别题作新华路315号和185弄1号，两栋原始地块形心相距207.1米。[同页两栋的题签与地块](two-xinhua-addresses.json)[史料与定位](../../../source/precise/changning-xinhua-lane-185-no1/README.md) [独立模型](../../../xinhua-lane-185-no1.html)

原始GLB与实际解码的近、远两档，每档采样90处。检查包括三道廊口和四个支承、九片花栏的实体交叉及左右镂孔、后部门扇、修后钢窗、棚式老虎窗及三座烟囱。第一次屋面测试发现主屋瓦坡遮住老虎窗下部四个采样点，调整外挑与下槛后复测均命中窗体。对照四普原图还校正了低西翼朝庭院的瓦坡，三个横向采样点均命中瓦面。Blender工程重新打开后逐面、逐材质与原始GLB吻合。1200×680原生取景中，左侧低翼的通长瓦檐、三跨外廊、山墙与右端主楼均在画内。左右各留5.75%，屋面上方与地脚下方各留14.39%。[原生正面图](changning-xinhua-lane-185-no1-preview.png) [三档网格](surface-checks.json) [原生与压缩](geometry-native.json) [棚窗前后对照](dormer-revision.json) [西翼瓦坡前后取样](west-wing-and-camera-review.json) [原生取景边界](native-camera-bounds.json)

实取四组近景子瓦片与远景几何，单独检查1号主楼2392、5号入口与7号招待所周围七幢建筑。地面碰撞在三个券廊下保留通路，柱脚、主楼与西侧低翼保留实体。[近远与地面](placement-geometry.json) [地图契约](final-placement-contract.json)

按真实桌面、手机视口的默认相机，各对七个门廊、花栏、山墙和屋顶位置检查无遮挡视线。[双端视线](overview-sightlines.json)

桌面与390像素手机各检验近景与简化远景，逐个下载四个正式文件并校验签名。[独立页面](viewer.json)

正式前后两个HTTP站上的目录、运行模块及模型文件均与冻结签名一致。[交付收据](signed-23k-http.json)

31183与31184两版主图显示，同一地块从普通城市楼体变为1号住宅。桌面与手机分别从目录真实点选，初始图中能辨主屋、较低的西翼和三座烟囱。近景复核了21个地面位置，远景加载了简化网格，并实取四个模型文件。[桌面初始](city-31184/desktop/map-desktop.png) [手机初始](city-31184/phone/map-mobile.png) [登记前](city-31184/before/map-before.png) [屋顶与老虎窗](city-31184/architecture/map-shed-dormer-roof.png) [远景及四件收据](city-31184/distant/main-browser.json)

原来从远处向南立面取景，中央视线被邻墙挡住。移到院内后，三道浅尖券、四处支承、券上花栏及后墙门窗可同时辨认。左下柱脚有一段被信息卡挡住。第一次院内图已捕获，随后尝试的斜角机位未通过地标牌命中检查；从目录重新进入的正面单次检查完整通过。[原视角](city-31184/architecture/map-south-arcade-railing.png) [院内正面](city-31184/courtyard/map-court-front-three-arches.png) [分镜与图像校验](city-31184/visible-architecture.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/4f86ac8af96f0f2f1190ecac35145d79cc046998/projects/shanghai/index.html#landmark=changning-xinhua-lane-185-no1&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
