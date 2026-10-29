# 崇明学宫名宦祠：文字尺寸参照候选

[独立预览](../../../minghuan-shrine.html) · [资产清单](../../../assets/models/candidates/chongming-minghuan-shrine/manifest.json) · [检查记录](../../../data/audit/minghuan-shrine-v1/README.md)

依据博物馆文字制作三开间、中央开门的基础外观候选，提供可编辑Blender与近远景GLB。**简单双坡单脊屋顶、两侧格窗、双扇门样式、低基座、灰瓦/浅墙/红褐木配色及侧后墙都是建模假设，未获得单体照片核验。** 瓦垄和门窗构件用于表达这套假设，不代表真实瓦数或精确门窗式样。未添加无依据的斗栱、碑文、匾额、雕刻或室内陈列。

## 文献及量测端点

[崇明县博物馆旧官网第1节“名宦祠 乡贤祠”](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_2.htm)记载：两祠各三楹、中间开门，东西各长8.8米、南北宽6.6米、高6.5米，1998年修葺。[崇明区政府2021年文章](https://www.shcm.gov.cn/zjcm/006008/20210423/8c183cc2-f5a9-4d52-b152-9d72ec7eb5a7.html)明确名宦祠在戟门东、乡贤祠在西。这是名称和相对位置依据，不能代替单栋地理配准。

文献没有说明长宽对应墙线、柱线、檐线或基座。本件选择如下解释，均保存在[设计输入](design-input.json)：

| 对象 | 本模型尺寸 | 依据或假设 |
|---|---|---|
| 基座外包 | 8.8×6.6米 | 将文献平面尺寸赋给基座，端点对应关系未核验 |
| 外墙外线 | 8.4×6.2米 | 模型估计，侧墙厚0.20米，前后墙与其内侧衔接 |
| 主屋面片 | 9.4×7.4米 | 模型估计的外挑屋面 |
| 全部构件实际外包 | 约9.55×7.542×6.5米 | 对导出GLB量测，包含檐口和瓦端；不是文献实测长宽 |
| 中央门洞 | 2.3米宽，模型标高0.2至3.45米 | 仅“中间开门”有文献依据，洞口尺寸及双扇板式估计 |
| 两侧格窗 | 每处1.6×1.65米 | 开窗位置、数量和格数均估计 |

最高点6.5米作为文字引导约束；不能因此宣称建筑已实测复原。局部正面设在模型-Y方向，仅供独立查看，不声称核验了实际门向。

## 单体身份与范围

[已有资料审查](../../../data/model-todo/chongming-shrines-reference-review.json)说明：现代航拍的戟门旁建筑受树遮挡，不能稳定识别名宦祠单体边界或屋顶。航拍东西远处的独立屋属于其他建筑轴线，不能据其外观冒认为本祠。1881年示意图也不能验证1998年后单体硬山、悬山或歇山形式。当前采用双坡屋顶是显式假设，并非“照片看见的屋顶”。有限搜索未取得已核验单体照片，不表示其他资料不存在。

两处格窗由有真实间隙的框格和后退暗面组成，不提供室内。后面不加无依据开口，以素墙闭合。材料为原创平色与粗糙度近似，无照片采样PBR；无照片再分发或嵌入。来源URL、读取日期、原文响应哈希和身份审查记录见[source-register.json](source-register.json)。

未包含戟门、乡贤祠、院落铺装和实测地面，未替换整座博物馆源轮廓，不增加40处原址漫游或逐栋照片复原完成量。独立室外漫游仅沿模型外围。不声称某次修缮后的准确形态或2026年现状。

## 构建

仓库根目录执行，依赖见`source/requirements.txt`；Blender 4.3.2、gltfpack 1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-minghuan-shrine/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-minghuan-shrine/source/build_model.py --out /tmp/minghuan-shrine
python projects/shanghai/source/precise/chongming-minghuan-shrine/source/build_model.py --out /tmp/minghuan-shrine --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-minghuan-shrine/source/build_native.py -- --raw /tmp/minghuan-shrine/chongming-minghuan-shrine-raw.glb --out /tmp/minghuan-shrine/chongming-minghuan-shrine.blend --previews /tmp/minghuan-shrine-previews
python projects/shanghai/source/precise/chongming-minghuan-shrine/source/package_assets.py --raw /tmp/minghuan-shrine/chongming-minghuan-shrine-raw.glb --lod /tmp/minghuan-shrine/chongming-minghuan-shrine-lod.glb --native /tmp/minghuan-shrine/chongming-minghuan-shrine.blend --out projects/shanghai/assets/models/candidates/chongming-minghuan-shrine --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/chongming-minghuan-shrine/source/verify_geometry.py --assets /tmp/minghuan-shrine --out /tmp/minghuan-shrine-geometry.json
```

原语及GLB写入器来源见`source/HELPER_PROVENANCE.json`；本祠平面和假设屋顶单独编写。Blender含可编辑网格与独立预览舞台，保存重开核对模型几何。原创代码与几何MIT。模型文件均小于100 MB。
