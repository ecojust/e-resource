# 赛华公寓临街立面复核

完整模型有33,436个三角面，远景为26,692个。Blender重新打开了67个可编辑网格，按材质核对过有向三角面的坐标。原始、网页近景与远景分别通过211条射线，覆盖两翼四组折面栏板与斜梯梁、七排窗、转角五层凸窗和最上部浮饰。[原生工程检查](geometry-native.json) · [独立射线](surface-checks.json) · [实照对照与估算项](visual-review.json)

模型仅替换1491的两条街侧窄带。原底图主体近景保留72.29%，远景保留72.58%。24个地面点覆盖商铺、路缘、斜角和原楼后部，两档均与周围建筑分离。默认桌面及手机机位各检查七个真实方位，涵盖四组楼梯及街角的底层、凸窗和浮雕。[两档落位](placement-geometry.json) · [相机视线](overview-sightlines.json) · [地图合同](final-placement-contract.json)

[建筑与来源](../../../source/precise/xuhui-savoy-apartments-street-front/README.md) · [单体预览](../../../savoy-apartments.html) · [原生、原始及两档网页模型](../../../assets/models/candidates/xuhui-savoy-apartments-street-front/manifest.json)

[桌面及手机、两档模型、四次下载](viewer.json)

最终目录以「赛华公寓常熟路、延庆路转角立面」登记在徐汇区。实际地点卡注明原名赛华、现名瑞华，并记载两翼各两处敞开楼梯及西北斜角连续五层的折面凸窗。独立页所用的地名、正文和图注均与本楼相符。资料记载1928年始建，模型取2020至2021年修缮后的街面。[最终单体页与真实地点卡](formal-26215-page-identity.json) · [页面错误内容回归](page-identity-negative-controls.json) · [原生工程及三档下载与实际网页的校对](formal-26215-viewer-http.json)

251处地点加入本楼后为252处。正式渲染程序复核四组楼梯、商铺及相邻地块的29处碰撞或裁剪位置。26k更正了其他单体页的一段文字，赛华公寓页、目录、四个模型文件及主地图裁剪输入均与25k相同。两份完整签名分别经1,524个真实HTTP文件逐一核对。[正式地图运行结果](city-25215/runtime-placement.json) · [各代地图及四件成品签收](release-http-summary.json)

制作报告生成器写入了通用的48次采样说明。该楼的相机脚本与最终渲染日志均记录12次Cycles采样，预览图来自重新打开的已交付Blender场景。[渲染配置与原日志](native-render-settings.json)

## 最终城市实拍

31214旧站的251处地点加入赛华公寓后，31215实测为252处。九场独立的公开页面分别验证旧街区、手机及桌面目录、正面与屋顶、手机放大、鼠标与触屏灯牌以及远景。近景实际渲染33,436面。远景以实测相机高度越过1,200米门限后加载26,692面，29个地面探点保留街沿和邻楼碰撞。主图的地点卡遮住街面局部，手机放大与独立页能更清楚地看到角窗和两翼楼梯。 [九张地图与四张单体实图](city-31215/visual-review.json) · [九次实退与四件下载](city-31215/slot-released.json) · [四次早先试拍的原始记录](city-31215/failed-attempts/index.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/829382f54780b4cf011fc48719fe65d213e44858/projects/shanghai/index.html#landmark=xuhui-savoy-apartments-street-front&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
