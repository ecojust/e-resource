# 峻岭公寓高层主体（锦江饭店中楼）

[在上海主地图查看](../../../index.html#landmark=huangpu-grosvenor-house&mode=overview) · [四件模型资产](../../../assets/models/candidates/huangpu-grosvenor-house/manifest.json) · [本轮检查](../../../data/audit/grosvenor-house-v1/README.md)

对象为峻岭寄庐／峻岭公寓，即Grosvenor House和锦江饭店中楼的历史高层主楼。文献明确记载1956年改名“茂名公寓”，因此这些旧称不重复制作成两座高楼。名录原拼写“峻林公寓、茂名公寓”保留在原始记录中。

## 资料与范围

[来源登记](source-register.json)和[文献复核](../../../data/audit/grosvenor-house-v1/documentary-review.json)记录实际取得的《上海名建筑志》峻岭公寓章节：五折环形、略带弧状，中央高、两翼阶梯降低，褐砖外墙与竖向分划。模型表现独立高层地上主体与有限宽度的入口雨棚，不包含华懋公寓、新锦江大酒店、礼堂、花园、独立低楼和室内。

官方章节记1934年建成、1935年出租，名录记1935年，分别保留不同事件口径。文献主楼地址记茂名南路59号，名录列65－125号范围；未取得足以对应各时期门牌和整处名录边界的证据，不静默修改原始地址。

文献记中央18层“包括地下1层”，两翼16、15、14、13层递降，高78米；另一百科记地上18层、地下3层，与之不同。模型选取78米作为作者总高约束，地上层段与退距按外观估计，不把地下层数直接叠成地上可见层，也不重建或认证地下空间。高度原文没有明确测量端点，冠顶、栏墙和楼层标高均非测绘值。文献建筑面积23985平方米不是占地面积，不用于缩放地图足迹。

文献另提高层西侧六幢三层公寓，其当前各栋身份和是否全部属于这条名录仍待调查。高层主体交付后，这部分范围调查继续保留在TODO，不将整条名录或整个锦江饭店标为完成。前庭雨棚左右另有两块未能从照片判明构造的原地图源范围，合计约35.04平方米；主图保留其原粗略几何，具体构造和高度继续调查。原近景在该处的24.7米估算屋顶不代表已核实建筑高度，也不为消除它而扩大新雨棚。

[照片复核](../../../data/audit/grosvenor-house-v1/photo-review.json)包括实际查看的2020年花园侧高位主图、2013年街景和远景、历史广景。主图可见中央高部、折线立面、露台和部分屋顶；街景显示旁边有独立低楼。它们不能提供完整背面、隐藏接口和全部屋面覆盖。部分图片页面误称“锦北楼”，已依据建筑体形与其他资料排除该错名；远景经过较强图像处理，不作为精确颜色依据。

独立源身份、方向、近似位置、前庭及邻楼保留范围见[定位复核](../../../data/audit/grosvenor-house-v1/footprint-review.json)。未见立面、屋顶布局、门窗数量与间距包含作者估计；模型不代表1934年原貌的逐面复原。

## 几何、许可与重建

墙体、阶梯退台、竖向饰线、窗框和入口构件采用原创几何。构件分别闭合，保留主要凹入空间，不表示整栋具备可进入的室内。商业字样、临时设施、街景人物及屋顶设备未逐项复刻。

提供原始GLB、网页GLB、远景GLB及可编辑Blender。实际面数、文件大小、作者尺寸和SHA256见资产清单与设计记录。主图提供全局俯瞰，未开放室内、地下和登楼。原生摄影棚、相机与灯光不属于导出建筑。

照片只供观察，不取样、不作贴图、不随资产分发。原创代码、几何与材质采用MIT，通用辅助函数来源见[source/HELPER_PROVENANCE.json](source/HELPER_PROVENANCE.json)；地图来源与ODbL署名见定位记录，参考照片分别保留其作者和许可。

Python依赖见[source/requirements.txt](source/requirements.txt)，另需Blender和gltfpack。从仓库根目录执行：

```sh
python projects/shanghai/source/precise/huangpu-grosvenor-house/source/build_model.py --out /tmp/grosvenor-build
python projects/shanghai/source/precise/huangpu-grosvenor-house/source/build_model.py --out /tmp/grosvenor-build --lod
```

原生保存、打包与复验命令见[本轮检查](../../../data/audit/grosvenor-house-v1/README.md)。后续模型变化须同步四资产、清单、定位合同和对应证据，保留相邻源楼体及之前交付记录。
