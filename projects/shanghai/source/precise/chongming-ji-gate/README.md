# 崇明学宫戟门：2005年照片与文献参照候选

[独立预览与模型室外漫游](../../../ji-gate.html) · [资产清单](../../../assets/models/candidates/chongming-ji-gate/manifest.json) · [检查记录](../../../data/audit/ji-gate-v1/README.md)

新增五开间戟门（大成门）外观候选：连续曲面瓦顶、瓦垄及瓦当、简化透孔脊带、中央贯通门洞、两侧红色实板门、外围白墙、圆柱与石柱脚、檐下椽条和檩条、蓝色无字匾额。屋面与门洞独立编写，没有把崇圣祠的歇山顶和格扇整栋缩放。

## 来源与可核验范围

[崇明县博物馆旧官网，第5节“戟门”](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_1.htm)记载五楹、东西长17.5米、南北宽6.6米、高8米及1998年修复。原文“内梁中三楹高，左右二楹略低”指内部梁架，**不能据此推断外屋顶分成三段高低屋面**；本模型采用2005年院落照片可见的一道连续瓦顶。

两张参考照片均由Joshua Wickerham摄于2005-09-02，Commons登记CC BY-SA 2.0：

- [Pan pool and Ji Gate of the Chongming Confucian Temple](https://commons.wikimedia.org/wiki/File:Pan_pool_and_Ji_Gate_of_the_Chongming_Confucian_Temple.jpg)：连续瓦顶、脊带、中央开门、两侧红门和白墙，树木、桥与前景遮挡低处及屋端。
- [Ji Gate of the Chongming Confucian Temple](https://commons.wikimedia.org/wiki/File:Ji_Gate_of_the_Chongming_Confucian_Temple.jpg)：仰视匾额、红色椽架、圆檩及瓦底。

[照片登记](public-photo-register.json)保存Commons元数据、原作者、许可、来源URL、读取日期、原图字节及SHA256；不在仓库再分发照片，不嵌入照片像素。网页提供原始来源链接。博物馆原文响应哈希及解释见[design-input.json](design-input.json)。没有可用的定标摄影测量和单栋地图轮廓。

文献长宽解释为低基座边界，尺寸端点未明确；高度8米用于模型顶约束，不等于实测精度。檐口、屋顶截面、瓦数、洞口宽度、门扇数量/细分、简化脊带孔洞、侧后墙、后面开间和门洞深度均含估计。源图没有充分覆盖后立面，后立面采用镜像开间估计。材料是原创平色/粗糙度近似，无照片采样PBR。未刻画精确匾额书法、花边、脊饰雕刻、室内陈列、树木、池桥、雕像与相邻建筑。

该模型未地理配准、不替换整个学宫源轮廓，不计入40处原址漫游或逐栋照片复原完成量。独立室外漫游沿建筑外围，虽然保留真实贯通几何门洞，现有外围碰撞仍不提供穿门/室内行走。历史照片与旧官网不代表2026年现状。

## 构建与检查

仓库根目录执行（Python依赖见`source/requirements.txt`；Blender 4.3.2；gltfpack 1.3.0）：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-ji-gate/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-ji-gate/source/build_model.py --out /tmp/ji-gate
python projects/shanghai/source/precise/chongming-ji-gate/source/build_model.py --out /tmp/ji-gate --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-ji-gate/source/build_native.py -- --raw /tmp/ji-gate/chongming-ji-gate-raw.glb --out /tmp/ji-gate/chongming-ji-gate.blend --previews /tmp/ji-gate-previews
python projects/shanghai/source/precise/chongming-ji-gate/source/package_assets.py --raw /tmp/ji-gate/chongming-ji-gate-raw.glb --lod /tmp/ji-gate/chongming-ji-gate-lod.glb --native /tmp/ji-gate/chongming-ji-gate.blend --out projects/shanghai/assets/models/candidates/chongming-ji-gate --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/chongming-ji-gate/source/verify_geometry.py --assets /tmp/ji-gate --out /tmp/ji-gate-geometry.json
```

Blender含可编辑网格、预览舞台和相机。保存重开核对模型几何哈希，不承诺Blender字节确定性。辅助几何来源与哈希见`source/HELPER_PROVENANCE.json`；原创代码与几何MIT，引用照片仍归原作者及其许可。
