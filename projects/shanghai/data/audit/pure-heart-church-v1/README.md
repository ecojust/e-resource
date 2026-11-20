# 清心堂主堂东北内庭

大昌街30号的主堂在1923年落成。中国基督教两会、上海文旅推广网和两组有日期的院落照片可以对照中央题额、双臂拱窗与围合平台的两趟室外石梯。原生工程重开后含82个可编辑网格。近景20,196面，远景13,280面。三档文件各通过77条射线，逐级检查两趟十七级台阶、栏板压顶、宽窄木窗、三字石额与中央门洞1.74米的可通行深度。[原件、署名与年代](../../../source/precise/huangpu-pure-heart-church/README.md) · [四件模型](../../../assets/models/candidates/huangpu-pure-heart-church/manifest.json) · [打开独立页](../../../pure-heart-church.html) · [原生预览图](huangpu-pure-heart-church-preview.png) · [原生工程校验](geometry-native.json) · [三档射线](surface-checks.json) · [照片核对](visual-review.json)

城市近景保留具名主堂338的90.17%，远景保留90.41%，四处截口与原屋面衔接。相邻独立分组的实际近景和远景距裁片最近1.24米和1.31米。地面判定保留内庭铺地和真实门洞的进入空间；两趟外梯、近墙与门洞尽端占地约67.21平方米。街口钟楼和历史校舍属于本次外墙之外的实体。[配准合同](final-placement-contract.json) · [近远分件和地面](placement-geometry.json) · [地图场景样点](map-case.json)

默认相机朝向200°，俯仰27°。在900×650和390×844的视口中，按冻结建筑体量计算的八个目标有六个可见，包括中央门洞与堂额。东侧相邻楼2010会挡住东翼的外端；另一个接近正俯视的角度可露出八个目标，但会压缩门洞和窗的可见高度。[两视口视线与邻楼记录](overview-sightlines.json) · [重算程序](check-overview-sightlines.py)

176处全城目录承接含四川南路若瑟堂的175处版本。实际执行城市裁切程序后，清心堂向338所属近景组加入七个裁片，邻组保留。独立页及四个文件通过真实HTTP下载校验，冻结目录873项的传输和SHA-256均相符。[城市运行时](runtime-placement.json) · [独立页下载](standalone-http.json) · [冻结目录传输](frozen-http-summary.json) · [登记增量](inventory-increment.json)

## 正式城市实景

从175处旧站到176处新站，同一机位看见灰色庭院转角换成了两翼红砖拱窗，中央题额下留有入口，台阶沿两侧下降。编辑范围止于庭院立面，旁侧楼房及主堂其余屋面保持底图形状。手机默认取景时，东侧邻楼挡住东翼外端；按一次加号可分辨台阶栏板、门洞和宽窗。桌面展开目录时，地标牌盖住北侧宽窗的一个采样位置，门洞和堂额仍在牌外。从屋面斜角只能看见一段墙顶，四个独立页视图可查看完整的东北内庭。[旧站同机位](final-map-24138/map-before.png) · [新站同机位](final-map-24138/map-street-facade.png) · [手机放大](final-map-24138/map-mobile-public-zoom.png) · [桌面默认](final-map-24138/map-desktop.png) · [实际投影与遮挡位置](final-map-24138/facade-witnesses.json)

从目录用键盘搜索“若瑟堂”时，清心堂及其局部裁切卸载，搜索“清心堂”可返回。16个地面位置中，中央题额下及其后的入口净空可通行，尽端、两梯与砖墙能阻挡移动，四处独立邻楼均保持碰撞。近景只裁338号的7个三角片，实际加载4段封边，并将远景切换到简化档。独立页在1250×820桌面和390×844手机各实点近、远两档；四个文件均经过浏览器下载、保存和逐字节核验。[键盘返回](final-map-24138/map-returned.png) · [城市检查细节](final-map-24138/main-browser.json) · [独立页四图及四下载](viewer.json) · [独立页桌面](viewer-desktop-full.png) · [独立页手机](viewer-mobile-full.png)

此版正式站点的883个签名输入共834,133,249字节。首轮浏览器留存了前后10张图，周边城市模型及瓦片的48次请求因本地冻结底图缓存写满返回502，涉及34个不同网址。恢复两套底图缓存后，逐个实取这34个网址并与同一冻结提交的Git对象核对；另开浏览器复拍手机默认与全城远景，34个文件再次通过，页面、请求及控制台均无错误。[全站HTTP收据](final-map-24138/138-all-http.json) · [逐网址的恢复核对](final-map-24138/cache-recovery.json) · [恢复后手机](final-map-24138/restored-mobile-default.png) · [恢复后远景](final-map-24138/restored-distant.png) · [复测报告](final-map-24138/retest.json) · [结果汇总](final-map-24138/results.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/676052fc555609681b5f63f8bd2617aa64acc0ff/projects/shanghai/index.html#landmark=huangpu-pure-heart-church&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
