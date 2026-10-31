# 大新公司历史主楼外观

[在上海主地图查看](../../../index.html#landmark=huangpu-daxin-company&mode=overview) · [四件模型资产](../../../assets/models/candidates/huangpu-daxin-company/manifest.json) · [本轮检查](../../../data/audit/daxin-company-v1/README.md)

对象为南京东路830号大新公司历史主楼，现第一百货商业中心的旧楼。本件表现圆弧形西南高转角、竖向柱带与凹窗、低翼上部敞廊和几何花格、齿状檐部、叠置圆片冠饰及沿街雨篷。北侧B馆、东侧C馆和跨街连接属于另行核对的对象，不合并为本件，也不将此入口解释为整个商业中心完成。

## 资料与外观范围

[来源登记](source-register.json)和[文献复核](../../../data/audit/daxin-company-v1/documentary-review.json)记录实际取得的《上海名建筑志》大新公司章节：地址南京东路830号，1936年1月10日开业，十层钢筋混凝土结构，高42.3米，占地3667平方米，建筑面积28000平方米；外墙奶油色釉磁面砖，门面黑色花岗石，采用钢窗及大遮篷。该章节未说明高度测量端点，也未提供完整平面。名录的“1934年”保留为另一来源的建造年代口径，不改写成该官方章节已经确认的竣工日期。

[照片复核](../../../data/audit/daxin-company-v1/photo-review.json)记录实际查看的西南街景，现代外观以2025年照片为主要观察依据，早期照片补充沿街构造。照片均集中于南面、西面和西南角，不能作为四面独立覆盖。北面、东面、内侧屋顶和隐蔽附属构造采用有明确范围的简化估计；没有把后部未核实的天井、楼梯及屋顶设备推定为已知结构。

圆角与转折位置参照独立旧楼地图轮廓；地图面积与文献占地数字不相等，不将模型整体缩放到3667平方米。原址对应、相接楼排除及实际模型外包见[定位复核](../../../data/audit/daxin-company-v1/footprint-review.json)。模型属于近似定位的外观候选，不是测绘成果或1930年代原貌复原。

相接B馆与C馆的具体建造年代未核；本次按独立源身份和可见体量划定范围，不能只凭外观判定其年代。

作者选择42.3米作为模型高部的顶部标高，以文献数字约束总体尺度；这不表示文献的42.3米明确测至该冠饰。普通翼部、敞廊、高部楼层、窗轴、退距、雨篷和屋顶厚度均含作者估计。全部实际几何尺寸、作者标高及资产SHA以清单与设计记录为准。

## 几何与使用

立面、窗框、宽浅色饰带、弧顶窗、花格、廊柱和冠饰均为原创几何。窗面后退、上部廊道和冠部小孔以实际空间构造表现；构件分别闭合，不声称整栋已布尔合并为单个实体，也不表示可以进入室内。原生Blender中的摄影棚、灯光和相机不属于建筑导出体。商业字样、广告屏、临时设备和街景人物未逐项复制。

四资产包含原始GLB、网页GLB、远景GLB及可编辑Blender。近远景保持主要体量，远景简化细小框格与装饰。照片仅供观察，不取样、不作贴图、不随资产分发；许可、作者、固定版本和观察限制保留在来源登记中。

原创代码、几何与材质采用MIT；复用的通用几何辅助函数见[source/HELPER_PROVENANCE.json](source/HELPER_PROVENANCE.json)。地图轮廓来源及ODbL署名见定位记录。参考照片保留各自许可，不因作为观察依据而变成MIT素材。

## 重建

Python依赖见[source/requirements.txt](source/requirements.txt)，另需Blender和gltfpack。从仓库根目录执行：

```sh
python projects/shanghai/source/precise/huangpu-daxin-company/source/build_model.py --out /tmp/daxin-build
python projects/shanghai/source/precise/huangpu-daxin-company/source/build_model.py --out /tmp/daxin-build --lod
```

原生保存、打包和复验命令见[本轮检查](../../../data/audit/daxin-company-v1/README.md)。后续模型变更须同步四资产、清单、定位合同与对应证据；保留相邻源楼体和之前交付的模型。
