# 金陵东路6–8号的旧城对照

加入雷米洋行之前，城市目录共有319处。两次从原目录的法国邮船大楼入口进入旧城，在雷米地块机位分别检查街区材质与原有建筑轮廓。下表列出各场看到的内容和实际退出情况。

| 检查 | 画面与读数 | 实际退出 |
| --- | --- | --- |
| 街区材质 | 已加载12份颜色、法线和粗糙度贴图，共7,413,517字节。近档街区有三处抹灰材质采用原贴图。两次截图时分别已绘制9帧和11帧。［[整页](materials/registered-surfaces-before-vector.png) · [裸画布](materials/registered-surfaces-before-vector-webgl.png)］ | Chromium正常退出。核查程序记录了西面相邻分块延迟，退出码1。 |
| 建筑与矢量 | 实际矢量瓦片有1,979个建筑轮廓和73个建筑部件。浏览器查到雷米地块、法国邮船大楼及五户邻楼的七个多边形。已加载的法国邮船大楼近档为49,900个三角面。［[整页](vectors/registered-vector-building.png) · [裸画布](vectors/registered-vector-building-webgl.png) · [七处地块与原始范围响应](overture/tile-owners.json)］ | 保存画面后，Chromium在继续载入街区时被系统终止。核查程序退出码1。 |

旧城机位对准雷米地块。第二张图可辨被选中的法国邮船大楼卡片，96×90像素的裸画布难以辨认临江立面的细部。原有152处地标版本保有同一近档模型的870×660临江街景和屋顶图。临江画面可辨门楼、中央竖窗及两翼退低的层次，屋顶画面可辨女儿墙与前后台阶状屋面。［[临江街景](historical/map-street-facade.png) · [屋顶](historical/map-roof.png) · [两版模型校对](historical/cross-version-review.json)］

两份现场报告及两份退出记录保留退出码和错误正文。公开摘录省略机内堆栈位置，原件与摘录分别列有[文件摘要](original-receipts.json)。

在本目录执行 `python check.py`，可逐项复核图像、文件摘要、请求范围、地块标识以及两次进程记录。完整城市现场另行收录。
