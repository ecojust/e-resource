# 武康大楼东侧副楼临街面核验

八层旧主楼与五层副楼分属两份地图来源。此次以2020年2月的街景和2024年5月1834号门面的现场照为依据，制作两层砖墙及上三层横窗。模型与原生工程均保留书店开敞入口，并将内部未观察部分在约1.6米处截断。[建筑史与照片来源](../../../source/precise/xuhui-wukang-mansion-east-annex/README.md) [独立预览](../../../wukang-east-annex.html)

原始与网页近景各37,138面，远景22,956面，13种材质。原生工程已重开并与原始几何逐面比对。三个实际文件各有105项射线检查，涉及三排横窗、两端弧转、砖墙窗、12个上层设备罩、5个红色下层罩、1834门牌与开敞门洞。[原生校验](geometry-native.json) [逐档105个实测点](surface-checks.json) [原生预览](xuhui-wukang-mansion-east-annex-preview.png) [四件下载](../../../assets/models/candidates/xuhui-wukang-mansion-east-annex/manifest.json)

裁片只绑定320。原底图近景保留72.64%，远景保留72.72%。19个地面点覆盖人行道、门洞、下部展窗、庭院方向和后部旧楼。第一次测试矩形裁片触及西侧主楼V5三角面投影约0.012平方米，最后将临街西南角削去，三片着色三角面与V5原始、网页近景和远景均零相交。最终结果中，副楼模型与主楼原生近景相距0.090米，裁片与已交付武康大楼V5近景相距0.052米。[原城市两档和地面检查](placement-geometry.json) [裁片与碰撞](final-placement-contract.json) [旧主楼各档逐三角面检查](main-building-preservation.json) [双屏七条实测视线](overview-sightlines.json)

原生工程的窗带、转角、店招及门洞与沿街照片逐部位比较。[照片和模型对读](visual-review.json)

正式独立页在桌面和手机上切换两档并下载四份文件。[独立页实测](viewer.json)

[正式两代HTTP签收](signed-23k-http.json) · [全城运行时与地面保留](runtime-placement.json)

### 全城地图与独立页

旧城有235处地点，副楼所在街面显示原始体块。加入副楼后的236处目录可从桌面鼠标和390像素触屏打开。淮海中路一侧的两层红砖、三排浅色横窗和圆角都在地点卡上方。转动镜头后，1834号绿色门牌、“大隐书局”门楣和内凹的书店门口可读。街面的另一侧仍可见八层主楼的红砖与石拱。[旧城街面](city-31199/map-before.png) [手机普通入口](city-31199/map-mobile.png) [桌面普通入口](city-31199/map-desktop.png) [1834号门口](city-31199/map-1834-bookshop-threshold.png) [东端窗带](city-31199/map-east-curved-window-bands.png)

23处地面检查覆盖副楼门口、人行道、保留的旧楼和4个邻楼位置。限定原楼320的3个裁片按近远两档生效，八层主楼1235独立保留。桌面鼠标与触屏都从地图灯牌重新回到副楼。440×380远景使用页面的缩小按钮，取得22,956面的远景文件。这个比例下只能辨街区。独立页则在桌面和手机分别显示整面近景与远景，并实存原始、网页、远景和Blender四件。[主楼保持检查](city-31199/main-eight-story-preserved.json) [实际输入与地面](city-31199/main-browser.json) [远景操作](city-31199/distant-public-zoom.json) [独立页与下载](city-31199/standalone/viewer.json) [逐图记录](city-31199/visual-review.json)

首次手机访问时17项底图与旧建筑资源返回502。随后从原始服务和最终服务各完整读回17项，逐份核对Git对象与SHA-256。一次复跑在写出进程回执前中断。最终手机目录与其余各段均从正式服务取得页面与实图。[首次失败记录](city-31199/first-phone-http/main-browser.json) [34次复读](city-31199/first-phone-http/all-first-phone-failures-recovered.json) [最终逐段退出记录](city-31199/slot-released.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/86f8ca706a4cb14dd929eee203155dff577fc4a1/projects/shanghai/index.html#landmark=xuhui-wukang-mansion-east-annex&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
