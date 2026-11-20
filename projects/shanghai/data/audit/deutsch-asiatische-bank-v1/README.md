# 江川大楼（德华银行九江路营业楼）

九江路89号的早期建筑和1988年加层来自同一现址。58个可编辑网格表现两面街墙、三层高的科林斯柱与西北门楣。46条射线分别在原始、近景和远景资产上核对主门、窗层、两街柱廊及屋盖。[政府铭牌与街照](../../../source/precise/huangpu-deutsch-asiatische-bank/README.md) · [逐项射线](surface-probes.json)

原生替换只涉及1064，东侧2676所在的三栋建筑实测与新模型至少相距30.34厘米、重叠为零。备用矢量源由85部分构成；替换后保留72,137.69平方米。同时启用先前四川中路261号联合大楼的替换规则，两个底图集合各自返回的剩余几何仍逐项相同。[原生近远验证](placement-geometry.json) · [两栋同时裁切](vector-source-checks.json)

18101单体页的网页近景和远景均在桌面与390像素手机上正常切换。四张图都容纳整片九江路街墙、底层券窗、门柱与右侧转角。页面四个下载与正式清单逐项比对。[实机签收与下载](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png)

142处原场景中，同一组六栋的德华银行1064仍是原始粗模，只有已登记的2602号被裁切。143处新版在桌面和手机目录均可选中银行，近景只替换1064，旧2602的边界及另外四栋保留。两档均取得实际模型，13个碰撞点覆盖室内、路口、人行道和共墙两侧。六幅实机画面以及四种资源下载均有散列记录。第一组近景中，街对面的楼体挡住门口，另一张可从两楼间看到三层通柱和上部加层。[142处前态](map-before.png) · [143处桌面](main-desktop.png) · [手机入口](main-mobile.png) · [街道中的柱廊](three-storey-corinthian-colonnade.png) · [屋面与后期加层](original-fourth-storey-and-1988-additions.png) · [远景](distant.png) · [实机记录](main-map-browser.json) · [200个公开请求和4个登记记录的逐项校验](main-map-verification.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/462453332da2aeb50cb88b85130254aa7125810f/projects/shanghai/index.html#landmark=huangpu-deutsch-asiatische-bank&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)

从九江路、四川中路交叉口补拍的两张1280×800街面近景均由143处正式目录进入。第一张可辨西北斜角的门框、双扇深色门和三角门楣；正常选中名牌覆盖门楣左缘一小段。第二张沿九江路斜看四根巨柱，四枚柱头、上方檐口及两柱之间的窗都可辨。两张均已加载实际六实体近景组，原有的1064和2602照登记裁切。两张图对应同一完整近景GLB，网页目录、近景GLB和原生组的实际HTTP字节均通过校验。[路口门头](baroque-portal-from-jiujiang-junction.png) · [九江路柱头](north-corinthian-column-heads.png) · [机位、现场状态与资源校验](street-entrance-browser.json) · [复拍脚本](check-street-entrance.cjs)
