# 崇明学宫东庑：文字尺寸参照候选

[独立预览](../../../east-wing.html) · [资产清单](../../../assets/models/candidates/chongming-east-wing/manifest.json) · [检查记录](../../../data/audit/east-wing-v1/README.md)

依据旧馆文字中的七楹、26.74×7.7×8米制作独立长屋体候选，提供可编辑Blender和近远景GLB。**七等分立面、中央关闭双门、两侧各三处格窗、简单双坡单脊屋顶、配色、基座及侧后墙均包含建模假设。** 航拍只能提供长屋形态、灰瓦屋面与白色端墙的概括参照，未核验这些具体开口和屋顶端部。

## 文献与时代区别

[崇明县博物馆旧官网“两庑”](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_2.htm)明确东庑位于大成殿前甬道东侧，并记载：“1997年，上海市文物管理委员会又投资修复。现东西两庑各七楹，砖木结构，庑长各26.74米，宽7.7米，高8米，建筑面积共412平方米。”网页中的“现”属于旧馆文章时点，不证明2026年的现场状态。

同段的“清顺治以前，各有九楹，庑前有长廊，顺治十一年（1654）废于潮”属于更早历史。本候选采用七楹，不据旧句添加现代前廊、廊柱或九开间，也不声称现状没有前廊。现代前廊是否存在及其截面仍待核验。原祠用途涉及的神龛、牌位与展陈没有被复原为本件室内。

412平方米是**东西两庑合计**。26.74×7.7为单栋尺寸乘积205.898平方米，两栋合计411.796平方米，与文献412平方米取整相符；这只是算术口径核对，不能由此确定尺寸测量线。

## 尺寸端点与外包

文献未说明长宽在墙线、柱线、檐线或基座上测量。本件采用以下解释，参数见[设计输入](design-input.json)和[source/build_model.py](source/build_model.py)：

| 对象 | 本模型尺寸 | 依据或假设 |
|---|---|---|
| 基座平面外包 | 26.74×7.7米 | 将文献长宽赋给基座，端点关系未核验 |
| 基座高度 | 0.20米 | 建模估计 |
| 外墙外线 | 26.34×7.3米 | 建模估计，墙厚0.20米 |
| 主屋面片 | 27.54×8.5米 | 估计檐外伸，双坡片面 |
| 全部构件实际外包 | 约27.69×8.644×8米 | 量测最终GLB，含边脊和瓦端；不是文献实测长宽 |
| 立面分区 | 七等分，每份约3.763米 | 七楹有文字依据，等宽及分区位置为估计 |
| 中央门洞 | 宽2.7米，标高0.2至4.35米 | 中央位置、尺寸、双扇板门均为估计 |
| 六处格窗 | 每处2.35×2.45米，4列5行框格 | 开窗数量、尺寸、位置和格数均为估计 |

最高点8米是文字引导约束，不能因此声称完成了测绘复原。局部正面设在模型-Y方向，仅用于独立查看，未核实真实入口朝向。屋顶采用平直双坡和简单脊帽，不主张已确认硬山、悬山或歇山。瓦垄、搭接带和椽端用于表达估计屋面，不代表真实数量或精细构造。

## 图像与范围

[澎湃2021年文章](https://m.thepaper.cn/newsDetail_forward_11469862)中的[“崇明学宫航拍”](https://imagepphcloud.thepaper.cn/pph/image/117/259/21.jpg)可见大成殿前庭两侧的长屋顶、灰色屋面、单层檐线与白色端墙；照片拍摄时间未单独说明。677×478像素不足以判读单体屋顶端部、廊柱和门窗数。旧馆无题注廊道图无法可靠绑定东庑，未把其中红柱布局移植到本候选。有限检索的各图适用范围见[两庑资料审查](../../../data/model-todo/chongming-wings-reference-review.json)。未找到可核验完整立面的资料，不表示其他照片不存在。

六处格窗由封闭框格实体和后退暗面组成，格内存在真实间隙；中央门关闭。侧后墙采用素面封闭。未添加无依据的斗栱、雕饰、匾文、神龛、牌位、石像、展陈或室内。素材为原创平色与粗糙度近似，无照片采样贴图，无照片再分发或嵌入；图片与文字URL、响应哈希和观察限制见[source-register.json](source-register.json)。

本件不含西庑、大成殿、院落铺装或实测地面，未城市配准，未替换整座博物馆源轮廓。独立室外漫游沿模型外围，不提供室内参观。它不增加已完成原址配准或逐栋照片复原的数量。

## 构建

仓库根目录执行，依赖见`source/requirements.txt`；Blender 4.3.2、gltfpack 1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-east-wing/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-east-wing/source/build_model.py --out /tmp/east-wing
python projects/shanghai/source/precise/chongming-east-wing/source/build_model.py --out /tmp/east-wing --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-east-wing/source/build_native.py -- --raw /tmp/east-wing/chongming-east-wing-raw.glb --out /tmp/east-wing/chongming-east-wing.blend --previews /tmp/east-wing-previews
python projects/shanghai/source/precise/chongming-east-wing/source/package_assets.py --raw /tmp/east-wing/chongming-east-wing-raw.glb --lod /tmp/east-wing/chongming-east-wing-lod.glb --native /tmp/east-wing/chongming-east-wing.blend --out projects/shanghai/assets/models/candidates/chongming-east-wing --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/chongming-east-wing/source/verify_geometry.py --assets /tmp/east-wing --out /tmp/east-wing-geometry.json
```

通用构件和GLB写入器来源见`source/HELPER_PROVENANCE.json`。东庑长屋参数、七分区和开口假设单独编写。Blender包含可编辑网格及独立预览舞台，保存重开核对建筑几何。原创代码与几何MIT；模型文件均小于100 MB。
