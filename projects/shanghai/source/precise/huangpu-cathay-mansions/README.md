# 华懋公寓历史主楼（锦江饭店锦北楼）

[在上海主地图查看](../../../index.html#landmark=huangpu-cathay-mansions&mode=overview) · [四件模型资产](../../../assets/models/candidates/huangpu-cathay-mansions/manifest.json) · [本轮检查](../../../data/audit/cathay-mansions-v1/README.md)

对象为长乐路的华懋公寓，即锦江饭店北楼／锦北楼。表现花园侧褐砖长立面、浅色窗框和竖线、多边凸窗，北侧两处凸翼及其间凹入空间、顶部退台和低层外观。峻岭公寓、花园内礼堂、其他锦江楼栋、新锦江大酒店及和平饭店均为其他对象，不并入本件。

## 资料与范围

[来源登记](source-register.json)和[文献复核](../../../data/audit/cathay-mansions-v1/documentary-review.json)记录实际取得的《上海名建筑志》“高贵典雅的华懋公寓（锦江饭店北楼）”章节：公和洋行设计，王荪记营造厂承建，钢筋混凝土框架，一字形平面、北面凸出两部分，褐色面砖、浅色勾缝及石料窗框。正文记1925年动工、1929年建成，另段记1928年投资；保留原文不同叙述，不拼成未经证实的单一开工日期。

名录原条目记长乐路109号，文献及当前百科记189号。源名录原样保留，模型身份通过名称、街角、照片与独立地图轮廓交叉判断；两个门牌的历史对应关系尚未核实。资产元数据沿用的`current_address`字段填写名录109号，并不表示已经核实当前门牌；同处的`address_conflict_note`保留此限制。

同一文献记十四层、高57米，同时保留十三层、高65米的另一说法；两者都没有明确测量端点。模型采用57米作为作者选定的总高约束，层高分配、主体与退台高度、屋顶最高点及窗轴尺寸均包含估计，不将其解释为测绘标高。文献建筑面积21202平方米不是占地面积，不据此缩放地图足迹。

[照片复核](../../../data/audit/cathay-mansions-v1/photo-review.json)包括实际查看的2006年花园侧照片、2019年西北街角照片及两张历史照片。现代照片提供互补观察方向，花园侧下部受树木遮挡；东面、完整屋顶、北翼内侧和隐蔽连接没有完整独立覆盖。历史广景同时出现华懋与峻岭，用于区分两楼；未把峻岭的阶梯高冠或华懋老照中的历史屋顶棚复制到本模型。

模型只绑定北楼独立地图源。相邻楼、礼堂和花园保持独立，北侧深凹不封成矩形楼块。具体源身份、朝向、近似位置、模型外包和邻楼检查见[定位复核](../../../data/audit/cathay-mansions-v1/footprint-review.json)。地图轮廓和未见细部不是实测墙线，本件属于现存外观参照模型，不能作为1929年原貌或整个锦江建筑群的完成证明。

## 几何与使用

墙体、退台、凸窗、窗框及装饰均为原创几何，保留窗面后退与北侧凹入空间；构件分别闭合，不表示整栋已合并为单一实体或具备室内。未逐项复刻商业文字、临时设施、街景人物和屋顶设备。

提供原始GLB、网页GLB、远景GLB及可编辑Blender。近远景保留主要体量，远景减少细框格和小装饰；实际面数、文件大小、作者尺寸与SHA256见资产清单及设计记录。原生文件中的摄影棚、相机和灯光不属于建筑导出体。主图提供全局俯瞰，尚未开放室内和登楼。

照片只供观察，不取样、不作贴图、不随资产分发。原创代码、几何和材质采用MIT；通用辅助函数的复用来源见[source/HELPER_PROVENANCE.json](source/HELPER_PROVENANCE.json)。地图来源及ODbL署名见定位记录，照片分别保留来源登记中的作者与许可。

## 重建

Python依赖见[source/requirements.txt](source/requirements.txt)，另需Blender和gltfpack。从仓库根目录执行：

```sh
python projects/shanghai/source/precise/huangpu-cathay-mansions/source/build_model.py --out /tmp/cathay-build
python projects/shanghai/source/precise/huangpu-cathay-mansions/source/build_model.py --out /tmp/cathay-build --lod
```

原生保存、打包与复验命令见[本轮检查](../../../data/audit/cathay-mansions-v1/README.md)。后续变更须同步四资产、清单、定位合同和对应证据，并保留相邻源楼体与先前交付记录。
