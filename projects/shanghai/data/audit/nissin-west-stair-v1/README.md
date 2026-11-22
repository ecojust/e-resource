# 外滩5号日清大楼西端外梯

原有地图入口为中山东一路5号日清大楼。修订集中在广东路西端转入西墙的一段。2015年公开的近照能辨出平台、铁栏与墙上的两扇拱形气窗，街口远照则把楼梯放回大楼西端。2020年2月与2021年1月两期街景均能看到浅色踏步。梯侧小道的入口可见，暗处的室内去向仍待调查。[名录、照片和街景](../../../source/precise/bund05/revisions/west-service-stair/reference-review.json)

| 验证对象 | 结果 |
| --- | --- |
| 编辑用原始GLB | 154,972个三角面，27个梯面、铁栏、拱形气窗、窗扇及窗槛取样点通过 |
| 网页近景GLB | 154,972个三角面，同一组27点通过 |
| 网页远景GLB | 101,026个三角面，27点通过，沿用无照片的远景材质 |
| 旧近景GLB对照 | 同一组27点中4点能命中相同表面 |
| 原几何范围 | 网页近远档的六个边界值与原档一致 |
| 临江玻璃 | 原有六组窗的112片玻璃、1,344个带纹理三角面、448个独立UV坐标继续使用原来的CC0照片 |
| 其他作者构件 | 3,951个构件的材质、面与顶点签名相同。222个旧开口中的220个保留，两樘西侧原估计窗位改为窗扇及独立弧形气窗 |

[实际网格的表面检查](west-stair-surface-rays.json) · [原作与修订构件逐项比较](author-component-comparison.json) · [逐片玻璃解码比较](registered-glass.json) · [三档范围](angular-bounds.json)

编辑文件保留建筑网格、原照片、临江正面和西端外梯两个相机，以及可单独选取的外梯和气窗顶点组。支架、花铁、梯宽、进深及14级踏步的尺度来自照片估计。临江入口、建筑轮廓和原地标编号均沿用原登记。[西墙预览](bund05-west-service-stair-preview.png) · [原生文件重开结果](native-reopen.json) · [五处登记的重复执行校验](five-registries.json) · [四个成品文件](../../../source/precise/bund05/revisions/west-service-stair/manifest.json)

在前后两份276处目录中逐项核对，仅本栋的资产、面数和制作说明有变。其他275处的登记，以及本栋的地图位置、可步行入口、地块编号和边界均一致。外滩总表与两份单栋元数据同步指向新文件。[五份登记文件的具体字段](in-place-catalog-comparison.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 30 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/adea4fa80619345c5a63012d5fb4dffa61d82d0a/projects/shanghai/index.html#landmark=bund05&mode=walk) · [固定版本逐文件核对](publication.json)

首次在 master 检查 30 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
