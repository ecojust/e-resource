# 延安中路877弄22号门廊与木窗

以1941年名录的冒鹤亭住址及2021年发表的22号门牌近照核对本户。北门东侧一排的临街窗与成对门洞还可与2015、2017和2021年的街景互查。模型取中央对门靠东的一扇和伴窗，门廊以后的居室及其他住宅排另列。缩尺约宽3.68米、高3.10米，门槛进深按照片估计。[原照与题名](../../../source/precise/jingan-mofan-village-no22-entrance/reference-review.json) · [门址、年代与制作范围](../../../source/precise/jingan-mofan-village-no22-entrance/README.md)

原始及网页近景各3,696个三角面，远档1,692个。第一次导出时有一个网格名称超过Blender的对象名长度，已缩短名称并重新导出。Blender 4.3.2重新打开最终工程后核对26个可编辑网格。三份网格各通过59项射线检查，包括凹门廊的净空、门槛、椭圆与交叉铁条、格中空处、木窗、窗栅、门牌上的实体数字和侧墙投递口。[渲染图](jingan-mofan-village-no22-entrance-preview.png) · [原生重开与逐材质网格](geometry-native.json) · [177项射线](surface-checks.json) · [四件资产](../../../assets/models/candidates/jingan-mofan-village-no22-entrance/manifest.json)

原1275号源高27.30米，是城市场景的估高。本件按北面做有上下限的局部裁剪，街角同一源高于3.10米的24.20米均保留。实际地面处理约2.77平方米，原279.44平方米占地仍保有99.01%。中央门廊在模型范围内可步入，最深处回到原建筑的边界。在以实际分页显示代码运行的单栋预演中，近远两档均核对GPU纹理中的高度、28个地面样点、8个矢量裁剪项目及隐藏后的恢复。原城近景11928个面中，只对低处裁剪体相交的115个面生效。另有837个近景面即使落在这段平面内，也全在剪切高度之上。[原地块和排房位置](../../../source/precise/jingan-mofan-village-no22-entrance/footprint-review.json) · [合同](final-placement-contract.json) · [网格和地面结果](placement-geometry.json) · [运行时预演](runtime-preflight.json)

[独立模型页](../../../mofan-village-no22.html)

从独立页用鼠标和触屏分别点击临巷正面、斜看门廊和俯看门槛，共取得六帧。正面可看见窗、号牌和门廊，斜看能辨出两侧的进深和门槛位置。内室超出制作范围，门廊尽头从独立页可见背景。两种网页档的实际解码面数逐材质与原生校验相符，四项下载均逐件核对字节和SHA-256。[鼠标与触屏实测](viewer.json) · [桌面正面](viewer-desktop-full-front.png) · [桌面斜看](viewer-desktop-full-oblique.png) · [手机俯看](viewer-mobile-lod-above.png)

登记后全市由188处增至189处。原始189处目录与采用分所有者分页显示的最终189处目录分别做了同一组检查。最终场景的1,005项签名文件已从实际文件视图逐项复读，两档均使用登记的网页模型签名，测试原墙上限3.10米、门廊净空、两类矢量数据以及模型隐藏后的恢复。[登记增量](inventory-increment.json) · [原始登记后运行记录](raw-registered-runtime.json) · [最终分页运行记录](runtime-placement.json)

在24151旧图的同一巷内机位，只能看到原墙的普通窗洞。24152的正面能分辨红褐色窗栅、实体门牌“22”和门槛，斜面能看到门廊右墙及门楣的椭圆交叉铁花。正面图里的地点标签遮住了门楣上缘；全市远景用来确认远档切换，门牌在这档不能辨读。两次实际指针操作都从静安别墅25号进入22号，手机在390×844画布触摸，桌面在850×650画布点击。[旧图同机位](city-24152/before-lane-detail.png) · [临巷正面](city-24152/after-lane-detail.png) · [斜看门廊](city-24152/after-oblique-detail.png) · [手机点选](city-24152/after-mobile-label.png) · [地图实测与近远档](city-24152/city-after.json) · [指针事件和进程退出](city-24152/process-exits.json)

两个站点分别有188处与189处，最终1,010项签名文件经HTTP逐项校验。交付版的独立页另由桌面和手机实拍六帧，点击保存的四份文件与清单一致。城市近远档均核对28个地面样点，裁剪只在门槛至3.10米高一段取代1275号底图，左右八栋邻屋保留。[前后两站](city-24152/two-signed-sites.json) · [全量HTTP](city-24152/all-http.json) · [地面和裁剪](city-24152/real-runtime.json) · [独立页六视图与下载](city-24152/viewer/viewer.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/09464df04fc401feff9e90052775ac8932457bc2/projects/shanghai/index.html#landmark=jingan-mofan-village-no22-entrance&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
