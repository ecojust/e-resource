# 永嘉新村15号拱廊与东端山墙

2014年的门牌照片、同日两张里弄照片和两期屋顶影像共同确定永嘉路580弄15号。此户位于西侧两层连排住宅东端。小门廊前面两拱、侧面一拱，绿色15号牌挂在东侧拱口旁，面向弄道的两层窗墙和矮花墙向东延至起伏山墙。窗框、花格和山墙轮廓按照片比例建模。[照片与年代](../../../source/precise/xuhui-yongjia-village-no15/README.md) · [门牌与屋顶位置](../../../source/precise/xuhui-yongjia-village-no15/number-and-roof.json) · [单体浏览](../../../yongjia-village-no15.html)

网页近景与原始GLB各8,396个三角面、远景4,164面，共12种材质。Blender 4.3.2重新打开编辑文件后，52个构件网格逐材质与原始版比对。最终版将屋面端部退入山墙，加上花墙孔洞的翻边、窗下雨篷支架和排水管细节。三档最终文件分别进行48次几何检查，包含门廊三向券口、门牌底和数字、花墙透孔、东端屋面收头及窗洞。[最终原生预览](xuhui-yongjia-village-no15-preview.png) · [第一版预览](preflight/first-native.png) · [原生与网页文件核验](geometry-native.json) · [144项构件检查](front-checks.json) · [四件文件与哈希](../../../assets/models/candidates/xuhui-yongjia-village-no15/manifest.json)

冻结源4151同时覆盖多户连排房屋。15号的立面与东墙从原近景切出13.10平方米，保留90.49%；远景切出12.12平方米，保留90.94%。两档保留部分与建模投影的交叠均为零。同源16、20、21号仍使用原生几何，另外五栋独立邻屋均无裁入。17个地面点覆盖弄道、院内空地、墙、门廊门槛、同排其他住户和邻楼。原城市体块屋顶高17.45米，照片所见两层山墙按6.84米估计，二者在剖面交接处按原源高度收口。[最终配准](final-placement-contract.json) · [原生几何、17个地面点与5个邻楼](placement-geometry.json)

默认角度在两种屏幕上分别进行静态遮挡测算。方位−74°、俯角25°时，保留的城市近远景没有遮住模型自身可见的拱廊、门牌、花墙和东山墙采样点。分母排除了模型自己遮住的部分。[256组屏幕与机位测算](camera-preflight.json)

1250×820桌面与390×844手机分别切换网页近景与远景，四张截图均能数出南窗三组、花墙透孔与门廊正面两个拱口。两种文件均保留绿色门牌；斜向原生图还能看到东侧折墙。网页实际下载的三个GLB和Blender文件逐一匹配清单中的字节数与SHA-256。[桌面近景](viewer-desktop-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png) · [四图与四件下载收据](viewer.json)

独立页斜向按钮改为“门廊与东山墙”。更名前后的三档GLB与Blender下载逐件相同。桌面与手机重新检查近远档，再从正面实际点击该按钮并记录视角变化。[新旧页面及四件哈希](viewer-label/caption-change.json) · [新版四个视图](viewer-label/viewer.json) · [桌面斜视](viewer-label/oblique-desktop.png) · [手机斜视](viewer-label/oblique-mobile.png)

自本栋首次登记的版本起，摄影角度按钮显示“门廊与东山墙”。第160项起的三个原站与各自六层正式入口均读回相同的修正页。[本栋实取页面](villa-viewer-caption-http.json) · [旧页、旧签名与改动范围](../dasheng-drummond-residence-v1/viewer-caption-correction/summary.json)

正式197处城市模块按近景绘制组仅为4151新增12个裁片，全城共1,028片、20个宏区，最高322片。本户所在近景组加入4151，旁组无变化。更正过按钮的正式站另外逐件下载页面、公共浏览器模块、清单与四件资产。[城市运行及独立地面采样](runtime-placement.json) · [正式站7项HTTP](viewer-label/production-http.json)

主图最终采用东侧弄堂内的实景视线。桌面鼠标和390像素手机触屏分别从地点目录选中永嘉新村15号，双拱、侧门洞和绿色“15”号均在地点卡上方。东侧近图还可看见窗格与花格墙角。院墙全貌可在独立页面斜视图查看。最初的静态测算忽略了部分城市楼体对镜头的实际遮挡，保留第一次进图画面和一次被邻楼挡住的手机试拍。正式地图共197处入口，对照上一版为196处。四种模型下载已逐件核对，最终站实取1,074份文件。[桌面主图](porch-map-31160/desktop-signed.png) · [手机主图](porch-map-31160/phone-signed.png) · [东向门牌与拱廊](porch-map-31160/desktop-east-facing-number-and-porch.png) · [东山墙与花格墙角](porch-map-31160/desktop-east-gable-and-garden-wall.png) · [第一次城图](first-map-framing/initial-review.json) · [主图与下载复核](city-31160/signed-routes-and-geometry.json) · [逐图观察](city-31160/visual-review.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/20727e4889de44c5f3a8272dda3c0d651ad022c7/projects/shanghai/index.html#landmark=xuhui-yongjia-village-no15&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，11 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
