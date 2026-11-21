# 淮海中路1768弄口住宅的模型与核验

市表2D011与墙上保护牌对应原淮海中路1754弄。这里显示2013至2015年照片所见的南门东侧住宅。临街宽9.49米的墙面分三层，可见底部两处浅拱、两组直顶窗、四扇弧顶窗和窗前护栏。2013年的绿牌近照记录「1768弄→／淮海中路」两行文字。[街景与屋顶来源](../../../source/precise/xuhui-huaihai-road-1768-residence/README.md)

已重新打开原生工程，逐材质对照全部网格。原始及网页近景 21,760 面，远景 12,512 面；三份模型分别通过35条独立射线。桌面及390像素手机各检查了两档，并实际保存下载四种文件。[原生检查](geometry-native.json) · [表面射线](surface-checks.json) · [四幅单体画面和下载](viewer.json) · [外观与页面文字](visual-review.json)

冻结近景原屋体共8,364面、远景12面，配准后两个源在裁片外残余面积均为零。七栋逐独立网格比对，最近的其他矢量轮廓离裁片 7.49 米。13 个地面探针覆盖住宅内、南门街侧空地及独立邻栋。最终默认镜位在900×650与390×844两种投影中均能看到绿色弄牌、上下窗组及檐口八个标志点。[配准与近远源](placement-geometry.json) · [地面与邻栋](ground-witnesses.json) · [视线](overview-sightlines.json) · [独立模型页](../../../huaihai-road-1768-residence.html)

可用仓库自带的三份脚本重跑几何检查。先按制作目录说明生成四件和解压 GLB，再从 projects/shanghai 运行下列命令。第三步会在两个设备尺寸上选择八个外墙标志均可见的镜位。

```sh
audit=data/audit/huaihai-road-1768-residence-v1
manifest=/tmp/lane1768-assets/manifest.json
python "$audit/check-surfaces.py" --manifest "$manifest" --decoded /tmp/lane1768-decoded --out /tmp/lane1768-surfaces.json
python "$audit/verify-placement.py" --manifest "$manifest" --work /tmp/lane1768-placement --out "$audit"
python "$audit/check-overview.py"
```

正式城市目录由263处增至264处。三个正式版本各自逐文件核验，并单独读取新旧两期的目录、独立预览页、可编辑工程和三档模型。本住宅保留832号建筑的独立登记与七座邻楼的边界。[正式站点与文件签名](served-release-layers.json)

## 正式城市地图复核

227号为霞飞别墅淮海中路1768弄口临街住宅。旧城从武康大楼东楼的目录项进入，复核时列263处。新站从目录及信标实际点选均打开本栋卡片，显示264处。手机触屏与桌面鼠标各完成一次信标点选，记录的落点均为本栋。

街面看到两组窗、窄铁栏和转入侧墙的窗。左下灰色浅券口旁挂有小绿牌，右侧为棕色门扇。近景中悬挂的地名标签覆盖门框的一小段，绿牌本身可辨，细小文字没有从这幅图转录。上层窗近照可见圆弧窗头、细分窗格及窗外栏杆，右侧窗回折到侧面。屋顶镜头显示前坡与转角处汇合的屋脊。远档中楼体融入路网。街面复核了13个本栋地面样点和7个保留邻体，10个城景的渲染与浏览器退出逐一查验。

独立页原有桌面、手机各两张截图，均已核过。近景21,760面、远景12,512面，两个门洞、窗头与屋顶轮廓在两档仍可辨。四种下载与两个站的实际文件摘要一致。视图原拍自28227，31227的页面、查看模块、清单及四个模型下载地址另经逐字核对。

[实机、地面与四种下载](city-31227/process-exits.json) · [旧城对照](city-31227/map-before.png) · [弄口窗墙及护栏](city-31227/map-street-windows-and-guardrails.png) · [弄牌和浅券](city-31227/map-enameled-lane-sign-and-lower-arch.png) · [远档](city-31227/map-distant.png)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/11935c2c68e8aa333a36b4690cd543815a45d8c4/projects/shanghai/index.html#landmark=xuhui-huaihai-road-1768-residence&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
