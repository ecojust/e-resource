# 新新公司南侧商店主楼临街外观

[在上海主地图中查看](../../../index.html#landmark=huangpu-xinxin-company&mode=overview) · [四件模型资产](../../../assets/models/candidates/huangpu-xinxin-company/manifest.json) · [本轮检查](../../../data/audit/xinxin-company-v1/README.md)

对象为南京东路720号的新新公司，现第一食品商店。本件表现南侧商店的南立面、两侧前段、竖向柱带、凹窗、上部环廊、中央两级空心方塔及南侧街角小亭。北侧旅馆、未知天井、室内与真实南北分界未建，继续保留原底图和后续任务；模型后切面仅作展示封口，不是经核实的后立面。先施、大新及新老永安均为其他建筑，不并入本件。

## 依据和范围

[来源登记](source-register.json)及[文献复核](../../../data/audit/xinxin-company-v1/documentary-review.json)记录实际取得的上海建筑志正文：南京路南部七层、高“30余米”，北部沿街延伸至天津路，贵州路设旅馆入口；1925年建成、1926年开业。官方全文未给出北旅馆层数、南北分界、天井平面或高度测量端点。

[照片复核](../../../data/audit/xinxin-company-v1/photo-review.json)记录2013至2025年八张实际查看的照片，其中部分是近似角度，不能当作八面独立覆盖。它们支持现存南部立面、柱带、墙面浅线脚、挑出阳台、铁栏杆、中央两级镂空方塔和南角小亭；不能证明北旅馆与背面已经照片核准。照片仅供观察，不取样、不作贴图、不随资产发布，作者、许可和固定版本见来源登记。

文献称南中塔1949年拆除，现代照片却有现存塔楼；复建年代和是否沿用原构造尚未核实，因此本件按现代照片制作，不宣称重现1925年原貌。文献“六楼挑阳台”与本件依据照片分配的层段亦不强行统一。立面轴数、窗格、栏杆花式、屋面与退距包含作者解释。南部屋面采用展示性盖板，不据此排除实际建筑存在尚未查明的内院或采光空隙。

模型选择主体挑廊层底约25.6米、廊顶29.2米、南角亭顶33.35米、中央塔实体顶37.5米作为设计标高。实际外包约51.750×30.862×37.500米；这些数字来自作者几何，不是实测尺寸，也不把文献“30余米”解释成经确认的37.5米端点。

本件采用原始整源局部坐标 `y ≤ -8 m` 约31米进深作为展示范围，**这条截断不是实测墙线或已经确认的历史商店／旅馆分界**。为使地图灯牌落在已建部分，最终模型原点移到南部范围的面积中心，世界位置保持不变；最终模型坐标与原始整源坐标的转换见[定位复核](../../../data/audit/xinxin-company-v1/footprint-review.json)。北侧约六成源足迹继续保留，不能将本件入口数量解释为整栋或整个源对象完成。

## 几何、许可和使用

浅色立面、凹窗、框格、墙板、柱带、挑台、托臂、栏杆及塔亭由原创几何构成；中央方塔保留真实通透空隙。近远景使用同一主要体量，远景简化细小框格和装饰。原始GLB、网页GLB、远景GLB与可编辑Blender的实际外包、字节数和SHA见资产清单。

作者构件分别闭合，不代表全楼已布尔合并为一个实体；凹窗、入口和敞廊也不表示已支持进入室内或登楼。原生文件中的摄影棚、相机和灯光不属于建筑导出几何。商业招牌、广告、旗帜和临时设备不逐项复刻。

原创代码、几何与材质采用MIT；通用几何辅助函数的复用来源见[source/HELPER_PROVENANCE.json](source/HELPER_PROVENANCE.json)。地图轮廓的来源与ODbL署名见定位记录；参考照片保留各自许可，不因观察而改成MIT素材。

## 重建

Python依赖见[source/requirements.txt](source/requirements.txt)，另需Blender与gltfpack。从仓库根目录执行：

```sh
python projects/shanghai/source/precise/huangpu-xinxin-company/source/build_model.py --out /tmp/xinxin-build
python projects/shanghai/source/precise/huangpu-xinxin-company/source/build_model.py --out /tmp/xinxin-build --lod
```

原生保存、打包、几何检查和浏览器检查命令见[本轮检查](../../../data/audit/xinxin-company-v1/README.md)。后续调整须同步四资产、清单、源足迹部分替换合同及相应证据，保留尚未建模的北侧源几何。
