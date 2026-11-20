# 银行公会大楼香港路立面核验

房管局第二批名录2A022及现场保护牌均指向香港路59号。2014年的独立街照和2018年发表的专题照片可互认三层街面、四根独立圆柱及两端壁柱、后退的59号门、花环及顶盾。三期航片和现行街道轮廓将临街柱列定位在地块2170北端。约4.2米以后的大楼采用剩余城市模型体量，中后段退台及窗型仍待进一步查证。[制作范围与出处](../../../source/precise/huangpu-bankers-association-building/README.md) · [原始照片记录](../../../source/precise/huangpu-bankers-association-building/reference-review.json) · [实际屋面及地块](../../../source/precise/huangpu-bankers-association-building/footprint-review.json)

网页近景及原始模型为34,016个三角面，网页远景为20,280面。独立解码后逐材质对照原始顶点和绕序。Blender重新打开工程并逐面检验，保有柱头叶饰、檐托与石花的独立编辑对象。每档49次射线分别检查临街与柱后窗、凹门玻璃、59号、花环、屋顶盾饰、柱身和架空街面，三份正式网格共147次。[实际四项交付](../../../assets/models/candidates/huangpu-bankers-association-building/manifest.json) · [独立页](../../../bankers-association.html) · [成品解码与原生工程](geometry-native.json) · [147次射线](surface-checks.json)

整面渲染在石阶上方可见五个开间。柱头近图能分辨两排石叶、带槽柱身和方顶，入口近图能看出玻璃、菱形气窗及59号牌的前后关系。比例按相片估计，石叶和盾饰线型是依据轮廓的几何概括。[整面](huangpu-bankers-association-building-preview.png) · [柱头近摄](column-capital.png) · [中央入口](central-entrance.png) · [原图对照和三个成像收据](visual-review.json)

最接近的独立建筑是东方的366号地块，真实近景与截取区仍有0.383米距离。实际近景替换约93.70平方米，原楼余下87.71%；远景替换约91.54平方米，原楼余下87.86%。21.65米长的交接线按原楼高度补面。碰撞区覆盖门后、墙和柱基，台阶、各开间及中央门前凹位可以通行。默认俯瞰方位220°、倾角38°，七个观察点的遮挡估算考虑了对街32米建筑。[完整配准和裁剪](placement-geometry.json) · [地图合同](final-placement-contract.json) · [视线估算](camera-sightlines.json)

在127处入口的地图上，通过 HTTP 实取带版本号的三份地图登记表，以及按 SHA-256 寻址的普通建筑总表、分区索引和替换表。共核对15个请求，返回字节与冻结清单一致。[逐次请求](metadata-cache-http.json) · [本次调整涉及的文件](runtime-input-changes.json)

在同一香港路镜头上，实测第126版的普通窗墙及第127版的五开间柱廊。手机和桌面各自从地图入口加载，近景中的圆柱、柱后窗墙、端壁和石檐可辨。沿街、俯视、远景均通过，地面16点逐一核对，街道路面、柱间通道与门前退廊均能到达，柱身、闭合门扇、实墙及四处邻楼阻挡相符。独立页实际切换两档，四件下载的字节均与清单一致。十张图均完整解码并绑定哈希。[地图前态](control-browser.json) · [地图后态](main-browser.json) · [单体页实测](viewer.json) · [逐图像素与目视复核](map-visual-review.json)

桌面、手机首屏及街面近景取自15085站，保留原截图与校验值。在最终18085站重新通过HTTP实取银行公会的单体页、放置合同、清单和四件资产。两个版本的银行公会整条城市记录相同，默认220°、38°、19.75级及占地、裁片和截口一致。最终127处目录里唯一改变的模型字段是提篮桥历史门楼首屏俯角由61°改为57°；另更新了窄屏全城灯牌的分组显示。[两份真实站点比对](final-grouped-map-http.json) · [原街面近景](map-street-facade.png)
