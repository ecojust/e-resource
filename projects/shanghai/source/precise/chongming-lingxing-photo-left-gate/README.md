# 崇明学宫棂星门照片左侧门（历史石框参照）

[独立预览](../../../lingxing-left-gate.html) · [资产清单](../../../assets/models/candidates/chongming-lingxing-photo-left-gate/manifest.json) · [检查记录](../../../data/audit/lingxing-left-gate-v1/README.md)

网页模型约0.23 MB，远景约0.05 MB，原始GLB约0.48 MB，Blender约0.26 MB。

本件制作照片左侧的独立门框：无字横梁及下部框线、两根伸高石柱、简化左上柱云纹和两扇近全开的窄红门。文献侧门宽2.3米、高3.2米解释为净洞口；柱截面、两柱约5.04米的总高、门角度及格板细分为估计。右上柱雕纹不可辨，保持简化光面，未复制中央门的两根雕花柱。

“照片左侧”是图像中的相对位置，尚不能据此确定其绝对地理方位，不称已核验西门。该件不含中央门、照片另一侧门、院墙、遮阳棚、门禁、人物、地面铺装或隐蔽托石雕刻。

## 两个年代的资料与差异

[2021年澎湃文章](https://m.thepaper.cn/newsDetail_forward_11469862)中的两张配图均作形态参照：

- “上世纪九十年代的崇明学宫”：照片左侧门有两根伸高石柱，门扇关闭。采用这一张的历史双柱石框关系，精确高度、截面及雕饰仍为估计。
- “棂星门”：左侧两扇红门近全开，内侧柱上方受树叶遮挡。采用这一张的开启关系，不把遮挡造成的短柱观感当作确有截短或改造的证据。

**本件明确组合1990年代石框与2021年开启姿态，不是某一日期的完整现状复原。** 没有证据确定柱顶是否经过改造；两张照片也不能支持准确施工尺寸。近侧视门面与遮挡使栅条数量、下部框格和门厚无法精确辨认，这些细节为原创估计。左柱浮雕以简化云纹表示，未复原精确龙纹。

[崇明县博物馆旧官网，第2节“棂星门”](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_1.htm)记载中门之外两侧门各宽2.3米、高3.2米；未指明测量线，本模型将其解释为净洞口，不把这些数值用于柱顶总高。

照片没有查到明确开放许可，仓库不再分发照片、不采样或嵌入照片像素。文章及图片URL、年代、SHA256、读取日期和解释保存在[照片登记](public-photo-register.json)及[设计输入](design-input.json)。模型石色、木色和粗糙度为原创近似，不是实测PBR或石材种类鉴定。

未地理配准，不替换整个学宫源轮廓，不增加40处原址漫游或整座棂星门复原完成数量。模型保留门洞及栅条真实空隙，独立室外漫游仍使用外围碰撞，不允许穿门入院。不代表2026年现场状态。

## 重建

仓库根目录运行，Python依赖见`source/requirements.txt`；Blender 4.3.2、gltfpack 1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-lingxing-photo-left-gate/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-lingxing-photo-left-gate/source/build_model.py --out /tmp/lingxing-left-gate
python projects/shanghai/source/precise/chongming-lingxing-photo-left-gate/source/build_model.py --out /tmp/lingxing-left-gate --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-lingxing-photo-left-gate/source/build_native.py -- --raw /tmp/lingxing-left-gate/chongming-lingxing-photo-left-gate-raw.glb --out /tmp/lingxing-left-gate/chongming-lingxing-photo-left-gate.blend --previews /tmp/lingxing-left-gate-previews
python projects/shanghai/source/precise/chongming-lingxing-photo-left-gate/source/package_assets.py --raw /tmp/lingxing-left-gate/chongming-lingxing-photo-left-gate-raw.glb --lod /tmp/lingxing-left-gate/chongming-lingxing-photo-left-gate-lod.glb --native /tmp/lingxing-left-gate/chongming-lingxing-photo-left-gate.blend --out projects/shanghai/assets/models/candidates/chongming-lingxing-photo-left-gate --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/chongming-lingxing-photo-left-gate/source/verify_geometry.py --assets /tmp/lingxing-left-gate --out /tmp/lingxing-left-gate-geometry.json
```

辅助网格原语和GLB写入器来源见`source/HELPER_PROVENANCE.json`；门框与门叶独立编写。Blender含可编辑网格及预览舞台，保存后重开核对模型几何；不承诺原生字节确定性。原创代码与几何MIT。
