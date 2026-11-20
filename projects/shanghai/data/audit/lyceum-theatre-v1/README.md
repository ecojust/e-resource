# 兰心大戏院

建模取茂名南路57号1931年剧场。市房管局第二批名录的原名及登记现名均为兰心大戏院，编号2C006。2012与2019的街角实照和《上海名建筑志》原文均支持二层三扇券窗、三层三扇方窗。金色中文招牌、深色雨篷、浅色阳台和墙角石采用这两个年份的外观。2020修缮效果图中的屋顶与侧立面英文招牌缺少对应的当年代竣工实照。[实物资料](../../../source/precise/huangpu-lyceum-theatre/README.md) · [原始来源](../../../source/precise/huangpu-lyceum-theatre/reference-review.json)

Blender重新打开88个可编辑网格，并逐材质回放70,804个三角面；网页近景同为70,804面，远景31,516面。每档用25条射线核对三个地面入口、上层三券窗、三联上窗、深挑石阳台、五个金色字、雨篷下通道、门厅平屋面、观众厅拱顶和后台高屋。建筑高度、背部与雕饰仍属估计。[模型正面](huangpu-lyceum-theatre-preview.png) · [原生文件对照](geometry-native.json) · [75项表面核对](surface-probes.json)

正式实体为14-13719-6694的2025号原楼，原始地图和当前OSM均单独标记兰心大戏院。实际展开的原生近楼1,680.22平方米、远楼1,668.94平方米均由该单体接替。新网格与东邻880号原楼近远均无重叠，还对880所在的全部六个原生对象整体检验，最小净距0.233米。东邻与原剧院轮廓共有约0.55平方米的数字化重合区，备用矢量掩膜保留了东邻和共同地面。兰馨公寓2448与238号邻楼分别保留。[实测几何](placement-geometry.json) · [备用矢量图块](vector-source-checks.json) · [11处地面坐标](map-probes.json)

独立查看器已在桌面和手机分别切换近景与远景，四个下载均与登记散列相符。正视图可辨底层雨篷下的三个门洞、二层三扇券窗、上层三联方窗和转角两侧的街墙。[查看器记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png)

两次场景之间，尚贤坊门楼、董家渡天主堂、原犹太人总会的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有234组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了13个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收9,677,279字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

121处主图已从区目录实点。桌面和手机默认视角均可辨角部门厅、券窗与拱顶。桌面名称牌盖住部分上层方窗，细部视角可看到其三联布局和石阳台。三个近景均只裁去2025，其他同组建筑保持原状。地面11点、远景与四项下载通过，浏览器记录无请求及脚本错误。[桌面主图](main-desktop.png) · [三券窗与雨篷](three-arches-and-marquee.png) · [弧形屋顶](auditorium-vault-and-stagehouse.png) · [手机主图](main-mobile.png) · [完整报告](main-map-browser.json) · [图像复核](map-visual-review.json)

在前一版120处的主图中，兰心地块近景组的6个建筑仍全部由底图绘制。加入剧院的121处版本仅裁切该组的2025号，六幅主图实测及153个真实HTTP资源均已核对。[登记前实图](map-before.png) · [前态记录](before-browser.json) · [输入复核](main-map-input-verification.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 36 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/5fa74e1b60f987c0b264c39208a663c0894c19dd/projects/shanghai/index.html#landmark=huangpu-lyceum-theatre&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 36 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
