# 浙一大楼两处街面

房管局2A040登记汉口路151号。上海地方志的江西中路222号和馆藏照片对应同一栋L形大楼的西营业厅入口、北办公入口。1948年陈植重新设计，1951年竣工。原始营业厅照片为西面开间提供依据，2019年航照、许一凡的街口全景与进门近照共同约束本次制作的现代外观。[来源与作者](../../../source/precise/huangpu-chekiang-first-commercial-bank/reference-review.json) · [门牌、年代及边界](../../../source/precise/huangpu-chekiang-first-commercial-bank/README.md) · [渲染对照](visual-review.json)

原始、近景均为39,474个三角面，远景20,198面。Blender存盘后重开核对78个可编辑网格。三份GLB分别通过124条射线，共372项，涉及水平窗带和外挑遮阳板、截角六排窗、上下错层的汉口路窗墙、通高楼梯窗、两扇门和西面三步台阶。模型照片中可识别的外部构件均为原创网格。[四份资产](../../../assets/models/candidates/huangpu-chekiang-first-commercial-bank/manifest.json) · [独立页](../../../chekiang-first-bank.html) · [网格与原生验证](geometry-native.json) · [渲染图](huangpu-chekiang-first-commercial-bank-preview.png) · [各档射线](surface-checks.json)

裁切沿江西中路、西北斜角和汉口路三处连续街面，旧1477的近、远投影各保留83.80%、84.13%。截口三段近远边缘的最大偏差约7厘米。近景无逐面来源标记，七个狭长三角须按三个顶点到各个地块的最大距离归属，并以远景的真实来源标记再次核验。同组其余53,702个近景面和两个邻组147,062、102,792个近景面均保留。最近的独立组近景距替换范围3.29米。地面在两处实际门扇前均保留可走的入口凹处。[地理控制](../../../source/precise/huangpu-chekiang-first-commercial-bank/footprint-review.json) · [实际城市网格](placement-geometry.json) · [放置合同](final-placement-contract.json)

### 银行门与保留办公楼的实际矢量结果

在154处地标的完整目录下，两套矢量底图在1477号原建筑各生成一份办公楼余面。西侧银行门位于被精模替换的外墙区域，作者坐标原点则仍在保留的办公楼内。国华银行149处阶段的原有检测保持同一结果。697个已冻结网页、模型与目录资源均经真实HTTP读取后复核了字节指纹。[矢量检查](runtime-placement.json) · [新旧程序与负对照](residual-probe/README.md) · [HTTP核对](frozen-http-summary.json)

从台湾银行所在的153处版本保留同机位前照，再从154处黄浦目录进入浙江第一商业银行。原正式视图的桌面、390像素手机、街角、屋面及远景模型均已加载。15个地面点以及近远城市瓦片、四件模型下载全部吻合。原桌面及手机默认镜头可见灯牌压住部分街面，收起侧栏后的街角图可见折角与长排窗口。[前态同机位](original-21116-map/before/map-before.png) · [原桌面与手机结果](original-21116-map/after/main-browser.json) · [街面](original-21116-map/after/map-street-facade.png) · [灯牌覆盖实测](original-21116-map/observed-sign-rectangles.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/8ff6d7a9de90f0cd9296c2339d4568a287cc44c9/projects/shanghai/index.html#landmark=huangpu-chekiang-first-commercial-bank&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
