# 麦加利银行东门门额石饰

同机位重开Blender原生文件，旧版上缘可见十六瓣圆花及平板；新版中央为素面近圆形石饰，两侧呈上下分格、端部支托和浅坡檐。门扇及下方两个小圆花来自原建筑。照片上未能辨明任何徽记或文字，此处保持素面。[修订前](door-before.png) · [修订后](door-after.png) · [相机和渲染签名](render.json) · [照片与原建筑代码出处](../../../source/precise/bund18/revisions/east-door-cartouche/reference-review.json)

近景130,220面，远景74,428面。逐一比较原始、网页、远景下的旧面顺序和索引、材质、照片、UV及整体边界，原圆花的面与其他建筑面没有交叉，共作48个正向射线检验，包括圆饰中心和边沿、墙面退深、两侧横框、顶檐和原门楣。原材质与贴图数据均沿用发行资产字节。重开原生档复核了其他既有网格、屋顶材质、UV和内嵌照片，以及受修改的原石材网格中每个保留三角的坐标、绕序、面材质与UV。[原始和近远档数据](geometry-comparison.json) · [原生重开](native.json) · [四件下载](../../../source/precise/bund18/revisions/east-door-cartouche/manifest.json)

原地修订接入后的全市地点数量仍为148。外滩18号沿用原入口，另外39条独立地标记录逐项未变。共637个冻结HTTP文件实取526,989,241字节。候选目录散列不变，普通地标表变为 `447f39a4c659e845` 开头。东门门额的街面复拍以同一经纬度及6.087米观察高度作为两代比较条件。[冻结清单](production-snapshot.json) · [逐件HTTP](frozen-http.json) · [街角相机参数](map-revision-case.json)

## 主图实拍

在正式148处的前后两代场景分别打开外滩18号，普通地标目录中的同一入口载入修订前近景130,374面、修订后130,220面。850×650桌面与390×844手机的默认视图均已截取，两代浏览器均无页面错误。每代还从实际HTTP核对普通地标、候选目录、运行脚本和四种下载。原网页模型散列以2d486e64711b开头，新网页模型以3789e554b68b开头。[前态及桌面和手机相机](main-map-before.json) · [后态及桌面和手机相机](main-map-after.json) · [两代各十项内容签收](108-109-final-21k-http.json) · [手机前态](main-map-before-mobile-default.png) · [手机后态](main-map-after-mobile-default.png)

从街面正对东门，俯仰77°、方位−94.55°、目标高度6.087米。两代使用相同相机，左边的原图能辨出十六瓣圆花，新图能辨出素面近圆石饰、两侧分格、端托和上檐。选中地标的灯牌挡住少量左缘，石饰中央和右侧支托可完整比较。把新增石材构件的三角面投影到同机位原图，合并覆盖13,715个像素，其中6,895个的最大RGB通道差达到6。投影外另有2,401个变化像素，包含旧形拆除、阴影和画面中其他差异。[左右同尺度对照](east-door-map-comparison.png) · [街面改前原图](main-map-before-desktop-detail.png) · [街面改后原图](main-map-after-desktop-detail.png) · [逐构件像素量测](real-map-geometry-pixels.json) · [可重算脚本](compare-map-detail.py)
