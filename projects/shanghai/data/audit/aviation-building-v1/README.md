# 中国航空协会旧址飞机楼：集成记录

> v6本地验收通过。v5网页曾发现灰屋面与石墙顶面共面，产生浅色碎斑；六组灰色屋顶／平台面下调约4厘米后，实际raw与LOD同高向上灰面／石面相交面积为0。8张新版原生图已由作者和独立审查人员实际查看，10张最终网页图已由QA和独立审查人员实际查看；同镜头确认碎斑消失、边缘连续。

[全局主图直达](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#landmark=yangpu-china-aviation-association-building&mode=overview) · [来源与范围](../../../source/precise/yangpu-china-aviation-association-building/README.md) · [四资产清单](../../../assets/models/candidates/yangpu-china-aviation-association-building/manifest.json)

西侧圆角宽翼与圆塔、三重厚石栏退台和顶部小圆体、低筒拱连接舱、东窄翼及中央后门阳台按修缮后照片制作；东西入口和门饰分别处理。前翼保留三道窗带，不将其解释为三个等高楼层。尺寸、隐蔽墙面和精细雕饰仍含估计。 原始与网页档分别为106,192和106,192个三角面，远景档60,384个；四资产共10,057,090字节，含可编辑Blender。模型最高约16.700米，为作者估计。

本楼位于长海路174号长海医院内，与同院旧市博物馆、现代医院楼和景观分开。1935兴建、1936落成、1991资助修缮和1993修复分别记录；1522平方米为文献建筑面积，不能当作占地尺寸。第三方图片仅作观察，不作为贴图或公开资产。实际读文及看图范围见来源目录的[文字记录](../../../source/precise/yangpu-china-aviation-association-building/documentary-review.json)和[照片记录](../../../source/precise/yangpu-china-aviation-association-building/photo-review.json)。

地图主源为1349，UUID `95d3bb45-e61c-4e87-a84c-4306362af0e6`。最终定位、显示替换和低位碰撞见[足迹核查](footprint-review.json)。仅新增该独立源的16行显示裁剪，全目录278／288行；其余模型登记及原有裁剪规则保留。

全局目录82处、16区，其中杨浦7处；40处保留原有漫游，42件候选使用俯瞰入口。两份README将本楼归入杨浦区，直接链接均指向主index。辅助页提供近景、远景切换与四资产下载。本楼已交付外观从活动制作队列移除，具体隐面、尺寸与雕饰限制继续保留在来源说明中。

本轮的增量资产清单和地图合同由[目录检查](catalog-checks.json)记录；此报告仅验证文件与静态登记，不代替原生模型和网页图像审查。作者与独立模型检查、最终浏览器结果分别见下文；公开发布另行记录。

[元数据与导航检查](metadata-checks.json)的9组命令全部通过，其中导航／目录12项、灯牌／俯瞰镜头35项通过。检查同时确认旧模型目录、资产登记、前35项制作记录和旧完成范围的记录值保持不变；本轮不重新解码旧模型资产。

作者的[封闭几何检查](author-geometry-checks.json)、[压缩几何核验](author-packaged-geometry-checks.json)和[独立目录重建](author-portable-rebuild.json)绑定最终资产。作者实际查看8张原生图，见[作者图像记录](author-native-visual-review.json)；作者图像与真实网页分别验收，范围各记。

[独立几何与8张原生图审查](independent-geometry-review.json)、[独立地图及低位碰撞审查](independent-placement-review.json)和[独立目录审查](independent-metadata-review.json)均通过。实际低位几何完整落入碰撞范围，17个邻体无交叠；两份README中建筑名称与模型ID的对应保留，新增飞机楼仅在杨浦区列入一次。独立图像审查者与作者分别记录各自实际看图范围。

v6修正的逐高度投影与接触射线见[屋面共面检查](author-roof-cap-overlaps.json)及[独立几何审查](independent-geometry-review.json)。三档实际GLB的完整XY三角多重集与0–2米低位三角多重集和v5精确相同；只有六个高程的灰色表面下调，定位、外包、碰撞、显示替换和邻体保护保持不变。更新后的四资产、地图合同和目录均已重新绑定，9组元数据／导航检查再次通过。

## 最终网页检查

[最终浏览器记录](browser.json)绑定v6清单及四资产，共10,057,090字节。完整／远景切换、辅助页四项下载、82条目录路由、82个灯牌的边界／点选与两种长标题布局、11个地面碰撞探针、原生触屏及鼠标点选均通过。主图实际近景仍含原4个owner，仅1349被本楼替换；医院邻楼保留。

10张最终截图由[QA](qa-pixel-review.json)与[独立审查人员](independent-browser-visual-review.json)分别逐张实际查看。与v5相同镜头的前后翼屋面及东门凸顶已无原共面碎斑或新增开缝；手机入框及密集灯牌也在实际图像中核对。各图裁切、标签遮挡与审查范围保留在记录中。

最终JavaScript错误、警告、HTTP错误均为0，WebGL错误为0且上下文未丢失；冻结输入逐字节保持一致。浏览器和本地服务已关闭。本轮记录为本地工作区的真实网页验收，Root实际看图和公开部署HTTP核对尚未在这些报告中声称完成。

## Root最终核对

[Root核对记录](root-review.json)绑定最终四资产及实际查看的8张原生图、10张网页图。圆塔相对前翼的位置、屋面接缝修复、双入口、桌面和手机入框、全城编号灯牌布局通过有界外观审查；17项浏览器冻结输入及17项元数据输入的当前哈希仍与已通过记录一致。照片尺度、隐面窗位与雕饰估计继续保留。公开HTTP核对在发布后另记。
