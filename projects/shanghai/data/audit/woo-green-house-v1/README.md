# 吴同文住宅（绿房子）核验

2016年花园照中的三层圆弧钢窗、带低墙的露台、最高层薄雨檐和通向草坪的外梯，是这次建模的主要依据。2013年4月发表的调查还记录了街侧楼梯窗、车道和四层平面。[制作与来源](../../../source/precise/jingan-woo-tongwen-green-house/README.md) [独立查看](../../../woo-green-house.html)

原始GLB和解码后的近、远两档各通过94个立面、窗框、车道、檐底和踏步射线检查。复开Blender工程后，几何顶点、三角形方向和材料与原始GLB核对通过。首轮图中可见底层窗框被玻璃掩盖，修订后窗框和实体柱处在玻璃前方，并补足上层曲线雨檐。[最终原生图](jingan-woo-tongwen-green-house-preview.png) [原始第一版图](first-native.png) [修订前后专项](native-revision.json) [三档射线](surface-checks.json) [原生及解码核验](geometry-native.json)

三组近景瓦片与远景再次核对，院南独立建筑2582距离最终裁片近景约0.76米、远景约0.86米，两个版本都没有误裁。被模型包围的底层横向车道在三个地面样点通行，居室及厅部的采样均阻挡。跨铜仁路两栋住宅、同仁大楼和多数原始房间保留。桌面、手机各有七个窗带、露台与楼梯点通过默认相机无遮挡检查。[实际网格和地面](placement-geometry.json) [放置契约](final-placement-contract.json) [视线](overview-sightlines.json)

桌面与390像素触屏实际切换近、远档并下载四种文件。截图和全项结果见[独立预览实测](viewer.json)。

修订后正式前后两个HTTP站抽取目录、控制程序与该模型四件，均与对应冻结签名一致。[正式传输](signed-23k-http.json)

### 正式城市地图实测

从213处旧城在同一地块取景后，在214处新城用1280像素桌面鼠标和390像素手机触屏从区目录进入吴同文住宅。花园侧能辨出弧梯、各层进深不同的水平露台和圆端连续弧窗。北京西路侧的近照能看到楼梯间的分层玻璃和竖梃，顶圈有一段被名称牌遮住。屋顶视角的左下层被保留的邻楼挡住。[同址旧景](city-31177/before/map-before.png) · [桌面默认](city-31177/desktop/map-desktop.png) · [手机默认](city-31177/phone/map-mobile.png) · [花园侧露台](city-31177/architecture/map-rounded-garden-terraces.png) · [北京西路侧楼梯间](city-31177/architecture/map-street-stair-lantern.png)

城市地图实测18个位置。底层横向车道的西、中、东三个测点可通行，四栋邻楼仍有碰撞。拉远后从正常目录打开独立页，四个下载按钮各保存了一件文件，共5,125,104字节，与登记指纹逐件相符。第一次旧城测试遇到系统内存不足；恢复后五段浏览器均正常退出。[地面与四邻实测](city-31177/desktop/main-browser.json) · [远景与四次保存](city-31177/distant/main-browser.json) · [逐图判读](city-31177/visible-architecture.json) · [首次中断的原日志校验](city-31177/first-control-interruption/log-proof.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/54a870c718eb8b3f0c01158956a72cafa77df467/projects/shanghai/index.html#landmark=jingan-woo-tongwen-green-house&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
