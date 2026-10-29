# 崇明学宫棂星门：中央石门框与门扇局部候选

[独立模型预览](../../../lingxing-gate.html) · [资产清单](../../../assets/models/candidates/chongming-lingxing-gate/manifest.json) · [检查记录](../../../data/audit/lingxing-gate-v1/README.md)

网页模型约0.65 MB，远景约0.07 MB，原始GLB约1.29 MB，Blender约0.54 MB。

本件只制作中央门框和两扇红色门叶：方形石柱、向上伸出的柱头、横梁及下部框线、简化云纹浮雕、两扇部分开启的栅门和下部实板。中央框内净宽3.35米、净高3.6米按文献解释设置；模型整体高度约5.85米、柱宽0.5米及门角度为照片引导估计。没有为该石门添加屋顶。

**两侧门仍待单独制作，本件不能代表整座棂星门完成。** 邻接院墙、石狮、地面铺装、背景戟门、原字刻及精确龙纹均未复原。柱头用原创云纹曲线表达浮雕层次，不把简化旋纹当作原有龙雕。

## 参考资料与时间

[博物馆旧官网，第2节“棂星门”](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_1.htm)记载“石框高耸，上刻云头纹”，中门宽3.35米、高3.6米，另有两侧门各宽2.3米、高3.2米。尺寸未说明测量端点，本件将中门数值解释为净洞口；不把侧门尺寸套到中央石柱或整体高度。

[Joshua Wickerham的2005年中央门框照片](https://commons.wikimedia.org/wiki/File:Lingxing_Gate_of_the_Chongming_Confucian_Temple.jpg)，Commons登记[CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/)，用于石框、横梁、柱头、红色竖栅及部分开启姿态。Commons标注日期2005-09-02，EXIF为2005-09-01 13:28:13；两者差异保留，未自行归一。照片裁切了地面和门扇下部。[2021年澎湃文章](https://m.thepaper.cn/newsDetail_forward_11469862)的“棂星门”配图补充了题字中央门下部实板的参考；该图左侧另一个敞开入口不纳入本件。2021年配图未查到开放许可，仅读取作形态参考，不在仓库分发或嵌入。

**模型是2005年门扇姿态与2021年下部实板参照的组合，不是某一日期的完整复原。** 下部框格细分、门叶数量之外的尺寸、开启角度、柱截面、后侧面及雕纹深度仍为估计。灰色石材、红木颜色及粗糙度是原创近似，材质名称不构成石材种类鉴定；无照片像素贴图或实测PBR。来源URL、作者、许可、读取日期、响应/照片SHA256及估计参数保存在[照片登记](public-photo-register.json)与[设计输入](design-input.json)，照片均未再分发。

原字刻虽可读，但本件未复制书法或添加替代字体。门洞与栅条之间是真实几何空隙；独立室外漫游使用既有外围碰撞，不允许进入门洞或院内。尚未城市配准，不替换学宫整院源轮廓、不增加40处原址漫游、不计入完整照片复原完成量。不声称2026年现状。

## 重建

从仓库根目录运行，Python依赖见`source/requirements.txt`，Blender 4.3.2、gltfpack 1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-lingxing-gate/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-lingxing-gate/source/build_model.py --out /tmp/lingxing-gate
python projects/shanghai/source/precise/chongming-lingxing-gate/source/build_model.py --out /tmp/lingxing-gate --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-lingxing-gate/source/build_native.py -- --raw /tmp/lingxing-gate/chongming-lingxing-gate-raw.glb --out /tmp/lingxing-gate/chongming-lingxing-gate.blend --previews /tmp/lingxing-gate-previews
python projects/shanghai/source/precise/chongming-lingxing-gate/source/package_assets.py --raw /tmp/lingxing-gate/chongming-lingxing-gate-raw.glb --lod /tmp/lingxing-gate/chongming-lingxing-gate-lod.glb --native /tmp/lingxing-gate/chongming-lingxing-gate.blend --out projects/shanghai/assets/models/candidates/chongming-lingxing-gate --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/chongming-lingxing-gate/source/verify_geometry.py --assets /tmp/lingxing-gate --out /tmp/lingxing-gate-geometry.json
```

Blender含可编辑网格、独立预览舞台与相机，保存后重开核对几何。辅助原语与GLB写入器来源见`source/HELPER_PROVENANCE.json`，不复用戟门或崇圣祠的整栋几何。代码与原创几何MIT；参考照片保留其作者及许可。
