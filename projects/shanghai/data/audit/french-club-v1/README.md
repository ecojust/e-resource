# 法国总会 · 花园饭店历史会所

市房管局第二批名录将茂名南路58号登记为法国总会，编号2C005。运营方保存的保护铭牌记载1924至1926年建造，1989年改建为花园饭店裙房。现状模型参照1927年花园正面照片、2010年代与运营方现状照片、二楼宴会平面及多期屋面影像。南昌路47号的老法国总会另列2C008。[来源与年代](../../../source/precise/huangpu-french-club/README.md) · [逐项参考资料](../../../source/precise/huangpu-french-club/reference-review.json)

南立面包括中央突出花园的五个拱窗、两翼各五跨上层柱廊、两端拱形山花及近照中可见的玻璃雨篷。东北翼依据二层平面和现状屋面塑造宴会厅轮廓。原图所见的两个屋顶圆亭已经消失。低层背部、雕饰、尺寸及材质色调仍属估计。[正面渲染](huangpu-french-club-preview.png) · [可编辑源](../../../source/precise/huangpu-french-club/source/french_geometry.py)

Blender重新打开286个可编辑网格并逐材质匹配142,818个三角面。网页近景保留142,818面，远景为78,400面。三档各用44条射线检查中央五窗、双排柱廊、雨篷下的地面通道及东北厅屋顶。[原生几何核对](geometry-native.json) · [132条射线](surface-probes.json)

实际近远景图块中，原低层裙房4860分别占4,908.07及4,884.55平方米，全部由新模型接替。展开北侧34层酒店塔3550的原始网格后，调整了新模型背墙和挑檐，近景与原塔留出0.47米，远景留出0.54米，投影重叠均为零。近景组中马路对面的3385至少离裁剪边界25米。行人碰撞包络按真实网格两米内的部分生成，保留玻璃雨篷下通道，覆盖三个支承柱。[几何与共墙核对](placement-geometry.json) · [契约](final-placement-contract.json) · [十二处地面坐标](map-probes.json)

备用OpenMapTiles图块还提供高度125米的独立高塔要素7575068970。以原始图块运行交付的裁剪代码后，塔楼与替换掩膜的投影交集为零，聚合要素中的街对面建筑仍保留961.71平方米。[备用图块实测](vector-source-checks.json)

115处冻结版本的267个输入已逐件通过HTTP 200读回，全部符合快照。单体页实测1250×820桌面与390×844手机，两种尺寸都能容纳南面全幅。近远景可见中央凸部的弧窗、两翼柱廊与端部窗墙。四份下载的字节数和SHA-256与清单相同。[完整HTTP记录](snapshot-http.json) · [单体四幅图及下载](viewer.json)

两次场景之间，尚贤坊门楼、董家渡天主堂的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有219组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了13个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收19,838,667字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)


115处主图从区目录进入。1280×800默认视图和手机默认视图均可看清花园一侧的圆凸厅及左右低翼。近景逐一打开五开间的西廊、弧面柱廊及宴会厅屋顶，三个视角均确认只裁去历史会所所占的4860，保留现代酒店塔3385及其他同组建筑。地面12点、远景切换和四项下载通过。此轮绑定原115处场景的140个实际HTTP资源和四项目录记录。[桌面主图](main-desktop.png) · [花园正面](garden-bow-and-five-arches.png) · [手机主图](main-mobile.png) · [图像复核](map-visual-review.json) · [完整运行](main-map-browser.json) · [字节复核](main-map-input-verification.json)

更新后的115处发布页面另从区目录进入并实拍，1280×800下花园立面和圆凸厅完整可见，名称牌位于建筑上方。四帧开场遮罩均已隐藏，地块4860的绑定及其精确掩膜与上一轮一致。此默认相机截帧时邻近原生细节仍在加载；上轮三个近景已逐项检查相同的共享组。[最终默认入口](final-overview.png) · [相机和地块记录](final-overview-browser.json) · [全部267个HTTP输入](final-snapshot-http.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 35 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/30073fb520857a3208e70130ea022be2a4cd6eee/projects/shanghai/index.html#landmark=huangpu-french-club&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 35 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)

前一版114处的同地块仍是底图粗楼。实测近景组同时含历史会所4860与现代塔楼3385，裁切清单为空。登记后的115处独立查看器可见舞厅所在的低翼与圆凸厅，主图在三个不同近景中只替换4860。[登记前画面](map-before.png) · [114处原生组与下载散列](before-browser.json)
