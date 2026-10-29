# 崇明学宫儒学大门：文字尺寸参照候选

[独立预览](../../../ruxue-gate.html) · [资产清单](../../../assets/models/candidates/chongming-ruxue-gate/manifest.json) · [检查记录](../../../data/audit/ruxue-gate-v1/README.md)

依据旧馆记载的长10.7米、宽8.8米、高8米制作儒学大门的独立基础外观候选。**文献未给开间、门窗数量或屋顶型制；三等分立面、中央闭合双门、两处格窗、单层双坡屋顶、配色和侧后墙全部是建模估计。** 当前资料没有已完整绑定的儒学大门单体照片，本件不采用仪门照片作为外观依据。

## 文献身份与年代

[崇明县博物馆旧官网第1节“儒学大门”](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_3.htm)原文记载：“位于棂星门东、仪门正南。”并记载：“2004年由崇明县人民政府投资修复，长10.7米，宽8.8米，高8米，建筑面积94平方米。”这些文字确定单体身份、相对位置和尺寸参照，未提供城市配准、实际门向或测量端点。

同段所述1760年修葺、1915年作为崇明县立初级中学校门属于历史记录，不用作现代门窗、匾额或用途的依据。2004年为文献所述修复年份，不等于唯一建造年份，也不能据此认定模型对应2004年完整形态或2026年现状。

10.7×8.8的计算值为94.16平方米，与文献94平方米取整近似；这一算术关系不能证明长宽测在墙线、柱线、基座或檐口。文献也没有明确长宽的地理方向，不能直接写成东西宽或南北长。

## 尺寸端点与外观假设

本件把文献长宽解释为局部X 10.7米、Y 8.8米的基座外包，局部正面设于-Y方向供独立查看；这是建模坐标选择，未核实实际入口朝向。参数见[设计输入](design-input.json)。

| 对象 | 交付参数 | 依据或假设 |
|---|---|---|
| 基座平面外包 | X 10.7×Y 8.8米 | 文献长宽的端点及局部坐标解释 |
| 基座高度 | 0.20米 | 建模估计 |
| 外墙外线 | 10.3×8.4米 | 建模估计，墙厚0.20米 |
| 主屋面片 | 11.5×9.6米 | 双坡屋面及檐外伸估计 |
| 屋面脊线／檐顶标高 | 7.75／5.5米 | 建模估计；素脊帽最高点为8米 |
| 立面分区 | 三等分 | 数量、等宽及位置均为估计，不能称文献已记三楹 |
| 中央门洞 | 宽2.6米，标高0.2至4.4米 | 中央位置、数量、尺寸及闭合双扇样式均估计 |
| 两处格窗 | 每处宽2.0、高2.1米，标高1.6至3.7米；3列4行 | 数量、位置、尺寸和格数均估计 |
| 全部构件实际外包 | 11.650000×9.741761×8.000000米 | 从最终GLB计算，依次为宽、深、高；含瓦端与脊帽，不是现场量测端点 |

简单单层双坡屋顶、灰瓦／浅墙／红褐木配色、后面素墙和屋顶端部封闭均为假设，不代表已核实硬山、悬山或其他屋顶类型。最高点8米是文字引导约束，不构成测绘复原。瓦垄、门板和窗格表达估计构造，不对应真实构件数量；不提供室内，也不添加无依据的牌匾或雕饰。

实现沿用[西官厅基础建模逻辑](../chongming-west-guanting/source/build_model.py)，来源 commit 为 `ffc4510616e628d505b710b8e834f4bb3571eb8a`。本件依儒学大门的独立文献尺寸调整基座、墙线、屋面和高度，并使用本件门窗参数。代码复用不证明两座实物样式或细节相同；仪门及官厅的照片、题名与历史不能转作儒学大门证据。

## 参考范围

[后续建筑资料审查第13项](../../../data/model-todo/chongming-later-buildings-reference-review.json)仅允许文献尺寸约束候选。现有全景和航拍可作空间线索，不能把画面右侧或背景建筑直接认作儒学大门；已题注“仪门”的照片属于另一单体。本件没有以该照片复制曲线端墙、门帘或窗柱布局。当前缺少已绑定单体照片不表示其他资料不存在。

材料采用原创平色与粗糙度近似，无照片再分发、嵌入或采样贴图。来源URL、原文、响应哈希及实现复用范围见[source-register.json](source-register.json)。本件不包含仪门、棂星门、明伦堂、院落铺装或实测地面，未作城市配准，未替换整座博物馆源轮廓。独立室外漫游沿模型外围，不提供室内参观，不增加原址配准或逐栋照片复原完成量。

## 构建

仓库根目录执行，依赖见`source/requirements.txt`；Blender 4.3.2、gltfpack 1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-ruxue-gate/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-ruxue-gate/source/build_model.py --out /tmp/ruxue-gate
python projects/shanghai/source/precise/chongming-ruxue-gate/source/build_model.py --out /tmp/ruxue-gate --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-ruxue-gate/source/build_native.py -- --raw /tmp/ruxue-gate/chongming-ruxue-gate-raw.glb --out /tmp/ruxue-gate/chongming-ruxue-gate.blend --previews /tmp/ruxue-gate-previews
python projects/shanghai/source/precise/chongming-ruxue-gate/source/package_assets.py --raw /tmp/ruxue-gate/chongming-ruxue-gate-raw.glb --lod /tmp/ruxue-gate/chongming-ruxue-gate-lod.glb --native /tmp/ruxue-gate/chongming-ruxue-gate.blend --out projects/shanghai/assets/models/candidates/chongming-ruxue-gate --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/chongming-ruxue-gate/source/verify_geometry.py --assets /tmp/ruxue-gate --out /tmp/ruxue-gate-geometry.json
```

通用构件及构建流程来源见`source/HELPER_PROVENANCE.json`。已交付可编辑Blender和近远景GLB，下表使用十进制 MB：

| 文件 | 大小 | 三角面 |
|---|---:|---:|
| chongming-ruxue-gate-raw.glb | 2.248732 MB | 28916 |
| chongming-ruxue-gate-web.glb | 0.738172 MB | 28916 |
| chongming-ruxue-gate-lod.glb | 0.092552 MB | 3684 |
| chongming-ruxue-gate.blend | 1.047415 MB | 28,916（模型几何） |

全部交付文件小于100 MB。两档源几何、最终压缩GLB解码、格窗与闭门射线、Blender重开、网页身份及近远景／视角／室外漫游检查均通过。网页局部窗旁可见极细竖线，列为显示限制，不增加照片复原或城市配准完成量。详细记录与三张原生预览、网页截图见[检查记录](../../../data/audit/ruxue-gate-v1/README.md)。原创代码与几何MIT。
