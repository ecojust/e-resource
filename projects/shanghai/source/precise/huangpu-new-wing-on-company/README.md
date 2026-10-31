# 新永安大楼主楼与后部外观模型

[在上海主地图中查看](../../../index.html#landmark=huangpu-new-wing-on-company&mode=overview) · [四件模型资产](../../../assets/models/candidates/huangpu-new-wing-on-company/manifest.json) · [交付检查](../../../data/audit/new-wing-on-company-v1/README.md)

本件表现南京东路627号的新永安公司／七重天大厦：北端高塔、相连的低楔形楼体、圆弧端部、竖向窗列、宽檐退台和阶梯形顶冠。南京东路635号老永安为另一件既有模型；两楼之间的跨街桥、邻楼及室内不在本件范围内。主地图采用近似定位，提供俯瞰查看。

## 资料与取舍

[来源登记](source-register.json)及[文献复核](../../../data/audit/new-wing-on-company-v1/documentary-review.json)记录官方建筑志的前楼22层、72米、后部8层、三角形基地1400平方米等描述。冻结地图轮廓约2016平方米，与文献面积口径未统一，没有通过缩放强行凑成同一面积。当前名录门牌627号与志书727号不同；1932、1933、1936年记载亦未裁定，本件不宣称复原某个确定落成年份的原貌。

[照片复核](../../../data/audit/new-wing-on-company-v1/photo-review.json)以实际查看的2025年两角度照片为主要形态参考，并对照2011、2013、2024年图像。北端窄正面、东北长面、宽浅色檐带、塔身竖列窗、顶部小体量、低翼圆端及温度计位置有照片依据。温度计只表现结构和刻度，不编造读数；广告、商业招牌、屋顶天线和多期杂乱设备未逐件制作。

文献没有给出完整平面、各层标高或72米的测量端点。模型将72米选作实体顶冠顶点，以前部13层、上塔7层、顶部2级服务体量解释22层：主要标高为23.4、26.6、42.6、65.7、68.3和72米。**这些层段分配、平面尺寸、退距、窗格和隐蔽面均为作者估计。** 后部8层以文字及照片中部分低翼为依据，背面、屋面不能视为已逐面照片核准。

高基座按照片中的东北连续立面与冻结底图边线采用近直角四边形；粗边线形成的约9度夹角差异尚未与文献“七层以上长方形”描述通过测绘统一。上部窄塔采用矩形阶梯体。低裙楼檐带在高基座处停止，避免在照片中连续的北端立面上添加一圈横檐。

## 几何与资产

模型使用独立编写的参数化几何，包含有深度的窗洞、窗框、玻璃、入口、竖向壁柱、檐带和顶冠；近远景保留相同主要体量，远景简化细窗框和曲线分段。原始GLB、网页GLB、远景GLB和可编辑Blender的字节数、SHA及实际外包见资产清单。

原创建模代码、几何和材质采用MIT；复用通用建筑几何辅助函数的来源见[source/HELPER_PROVENANCE.json](source/HELPER_PROVENANCE.json)。照片只供观察，不取样、不作贴图、不随模型包分发，各张作者、许可和固定版本在来源登记中保留。文献只保存事实摘要、出处和响应哈希。

作者构件分别闭合，未把全楼布尔合并为一个实体。窗洞和入口深度不代表已支持室内漫游、登阶或登楼；原生文件中的摄影棚地面、相机和灯光不属于建筑几何。

## 重建

Python依赖见[source/requirements.txt](source/requirements.txt)，另需Blender和gltfpack。从仓库根目录生成原始近远景：

```sh
python projects/shanghai/source/precise/huangpu-new-wing-on-company/source/build_model.py --out /tmp/new-wing-build
python projects/shanghai/source/precise/huangpu-new-wing-on-company/source/build_model.py --out /tmp/new-wing-build --lod
```

原生保存、压缩打包、几何检查及真实网页验收的命令和结果见[交付检查](../../../data/audit/new-wing-on-company-v1/README.md)。后续修改需同时更新网页与远景资产、清单、全局接入合同和相应检查，不以单独重建源模型代替主地图验证。
