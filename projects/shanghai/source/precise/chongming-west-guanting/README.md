# 崇明学宫西官厅：文字尺寸参照候选

[独立预览](../../../west-guanting.html) · [资产清单](../../../assets/models/candidates/chongming-west-guanting/manifest.json) · [检查记录](../../../data/audit/west-guanting-v1/README.md)

依据旧馆记载的东西宽7.4米、南北长10.2米、高6.5米，制作泮池／登云桥西侧西官厅的独立基础外观候选。**文献未给开间数、中央入口或窗数；三分区立面、中门、两处格窗、双坡单脊屋顶、配色、基座和侧后墙全部包含建模假设。** 本件不称“三楹”或“中间开门”已有文献依据，也未核验实际朝院立面的面宽。

## 文献身份与修缮记录

[崇明县博物馆旧官网第4节“官厅”](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_1.htm)记载：“位于泮池左右，分东官厅与西官厅两个部分，是古时官员休息的场所。”[崇明区政府2021年文章](https://www.shcm.gov.cn/zjcm/006008/20210423/8c183cc2-f5a9-4d52-b152-9d72ec7eb5a7.html)将东西官厅放在登云桥左右，并另述戟门东侧为名宦祠、西侧为乡贤祠。西官厅属于泮池／登云桥西侧的单体，不把戟门旁乡贤祠或大成殿前西庑当作本件。

旧馆明确区分两栋尺寸：东官厅东西宽6.5米、南北长10.1米、高6.5米；西官厅东西宽7.4米、南北长10.2米、高6.5米。两者不能等尺寸镜像。西官厅平面尺寸乘积75.48平方米仅为计算值，原段未列建筑面积，也未说明测量端点。

三组修缮记载分别保留：[旧馆文字](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_1.htm)记录1998年修葺；[澎湃2021年文章](https://m.thepaper.cn/newsDetail_forward_11469862)记录1991年对尊经阁、崇圣祠、东西官厅等建筑修缮，并记录1998年12月至1999年10月第二期工程包含东西官厅在内的多处建筑。这些是不同维修和工程范围的记载，不把任一年当作唯一建造年份或已核实的2026年状态。旧馆所述办公用途和历史“义路”名称也不代表已核实现今功能或匾额。

## 尺寸端点与造型假设

文献的东西宽、南北长不能直接等同于朝院立面面阔与进深。模型采用局部X长10.2米、Y宽7.4米，将长边设为朝院立面是建模解释；局部正面在-Y方向，未核实实际门向，未作城市配准。文献未给墙线、柱线、基座或檐线端点；本件选择将长宽赋给基座。参数见[设计输入](design-input.json)。

本件沿用[东官厅](../chongming-east-guanting/design-input.json)的三分区、中央关闭双门、两处格窗及简单双坡外观假设，来源 commit 为 `e84905881d151975e60cc9a0f334af186042629e`，基座、墙线和屋面改用西官厅参数。共用这套造型不证明两栋实物的开间、门窗、屋顶或配色一致；本件保留独立西官厅身份，也不为区分两件候选而编造新细节。

| 对象 | 本模型尺寸 | 依据或假设 |
|---|---|---|
| 基座平面外包 | X 10.2×Y 7.4米 | 对文献方位尺寸的局部坐标及端点解释 |
| 基座高度 | 0.20米 | 建模估计 |
| 外墙外线 | 9.8×7.0米 | 建模估计，墙厚0.20米 |
| 主屋面片 | 11.0×8.2米 | 双坡片面和檐外伸估计 |
| 全部构件外包 | 约11.15×8.339×6.5米 | 最终GLB实际量测，含瓦端和边脊，不是文献实测长宽 |
| 脊帽下方／檐顶标高 | 6.25／4.5米 | 建模估计；最高点约束为6.5米 |
| 立面分区 | 三分区 | 分区数量及位置均无文献依据 |
| 中央门洞 | 宽2.4米，标高0.2至3.55米 | 位置、数量、尺寸及双扇样式均估计 |
| 两处格窗 | 每处1.85×1.85米，标高1.35至3.2米；3列4行 | 数量、位置、尺寸和格数均估计 |

简单双坡单脊屋顶不构成已确认硬山、悬山或歇山的结论。瓦垄及门窗构件表达这套假设，不代表真实瓦数、开间或精细构造。后墙以素面封闭，隐蔽面仍待核实。

## 图像适用范围

[“崇明学宫航拍”](https://imagepphcloud.thepaper.cn/pph/image/117/259/21.jpg)只为泮池、登云桥两侧的低屋面组合、灰瓦和部分白墙提供院落上下文；树木和附建遮挡端部与立面。不能把整组屋面视为一栋文献官厅，也不能拿外轴建筑、大成殿前两庑或戟门旁两祠替代。泮池与戟门的正面照片同样不足以绑定官厅完整朝院立面，不能照搬其中的柱窗布局。

有限检索及各图限制见[官厅资料审查](../../../data/model-todo/chongming-guanting-reference-review.json)。本轮未找到新增的明确题注、可绑定官厅单体的完整立面照片，不表示其他资料不存在。图片拍摄时间与文章发布日期分别处理；所有照片仅作参考，无照片再分发、嵌入或采样贴图。材料为原创平色与粗糙度近似，具体颜色未核验。文字与照片URL、响应哈希见[source-register.json](source-register.json)。

本件不包含东官厅、泮池、登云桥、戟门、两祠、两庑、院落铺装或实测地面，不添加无依据的前廊柱、斗栱、匾额、雕饰、室内办公或展陈。独立室外漫游沿模型外围，未替换整座博物馆源轮廓，不增加原址配准或逐栋照片复原完成量。

## 构建

仓库根目录执行，依赖见`source/requirements.txt`；Blender 4.3.2、gltfpack 1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-west-guanting/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-west-guanting/source/build_model.py --out /tmp/west-guanting
python projects/shanghai/source/precise/chongming-west-guanting/source/build_model.py --out /tmp/west-guanting --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-west-guanting/source/build_native.py -- --raw /tmp/west-guanting/chongming-west-guanting-raw.glb --out /tmp/west-guanting/chongming-west-guanting.blend --previews /tmp/west-guanting-previews
python projects/shanghai/source/precise/chongming-west-guanting/source/package_assets.py --raw /tmp/west-guanting/chongming-west-guanting-raw.glb --lod /tmp/west-guanting/chongming-west-guanting-lod.glb --native /tmp/west-guanting/chongming-west-guanting.blend --out projects/shanghai/assets/models/candidates/chongming-west-guanting --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/chongming-west-guanting/source/verify_geometry.py --assets /tmp/west-guanting --out /tmp/west-guanting-geometry.json
```

通用构件、双坡屋面与立面构建逻辑、导出及验收流程沿用现有工具，见`source/HELPER_PROVENANCE.json`；与东官厅共用的外观假设及西官厅不同尺寸记录于[source-register.json](source-register.json)。提供可编辑Blender和近远景GLB，单个模型文件小于100 MB；实际几何及文件大小见检查记录。原创代码与几何MIT。
