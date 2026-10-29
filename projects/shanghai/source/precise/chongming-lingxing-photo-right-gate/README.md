# 崇明学宫棂星门照片右侧门（1990年代参照）

[独立预览](../../../lingxing-right-gate.html) · [资产清单](../../../assets/models/candidates/chongming-lingxing-photo-right-gate/manifest.json) · [检查记录](../../../data/audit/lingxing-right-gate-v1/README.md)

网页模型约0.023 MB，远景约0.018 MB，原始GLB约0.061 MB，Blender约0.114 MB。

新增历史照片右侧门的基础外观候选：两根简化光面伸高石柱、无字横梁与下部边框、两扇关闭红门、实体竖栅和下部实板。文献侧门宽2.3米、高3.2米解释为石框净开口；柱截面、约4.88米的整体高度、关闭姿态及格板细分为估计。没有把照片左侧门的云纹雕花复制到这件上。

参考照片在极右边缘，分辨率低且下部受裁切、遮挡，不能支持精确雕纹或门窗细部复原。因此保留清楚可辨的双柱框架及红色木门关系，把上柱处理为简化光面。此件不能称完整精细复原验收通过。

## 资料与年代

[澎湃文章《建筑可阅读｜崇明学宫：上海地区占地面积最大的孔庙》](https://m.thepaper.cn/newsDetail_forward_11469862)于2021-02-27发布，其“上世纪九十年代的崇明学宫”配图是本件主要外观参考。照片极右门框有两根伸高柱、较中央门低的横梁及下方深红木构；门叶下部不完整，关闭状态也只能作保守解释。

**2021年是文章发布日期，不能当作该历史照片的拍摄年份。** 配图仅说明1990年代，具体年份不明；没有证据确定它与1998/1999年前后修缮的先后关系，不声称恢复了某次修缮前或修缮后的完整状态。

同文“崇明学宫航拍”配图只用于核对中央门与两侧门布局，拍摄日期未知，不能用于门扇格数或石雕细节。另一张牌坊背景中的局部门框身份不能独立核实，未将其作为右侧门细节依据。“照片右侧”是图像中的相对位置，绝对地理方位待核验。

[博物馆旧官网第2节“棂星门”](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_1.htm)记载两侧门各宽2.3米、高3.2米；尺寸未指明测量线，本模型将其解释为净石框开口。柱总高、上下截面、顶帽、横梁厚度、门扇尺寸、六根竖栅/叶、下部板式、后侧面和铰链均为估计。

来源URL、图注、作者署名、读取日期、照片/网页SHA256和范围见[照片登记](public-photo-register.json)与[设计输入](design-input.json)。未查到开放图片许可，照片仅作形态参考，不再分发、不贴图。模型颜色与粗糙度为原创近似，未采样照片或实测PBR。

不含相邻院墙及漏窗、中央/左侧门、地面、前景绿植和精确石刻。尚未地理配准，不替换学宫整院源轮廓，不增加40处原址漫游或整座棂星门复原完成数量。门扇按关闭候选处理，中央及下部实板应遮挡；上部竖栅之间保留真实空隙。独立室外漫游沿外围，不允许穿门入院。不代表2026年状态。

## 构建

仓库根目录执行，Python依赖固定于`source/requirements.txt`，Blender 4.3.2、gltfpack 1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-lingxing-photo-right-gate/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-lingxing-photo-right-gate/source/build_model.py --out /tmp/lingxing-right-gate
python projects/shanghai/source/precise/chongming-lingxing-photo-right-gate/source/build_model.py --out /tmp/lingxing-right-gate --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-lingxing-photo-right-gate/source/build_native.py -- --raw /tmp/lingxing-right-gate/chongming-lingxing-photo-right-gate-raw.glb --out /tmp/lingxing-right-gate/chongming-lingxing-photo-right-gate.blend --previews /tmp/lingxing-right-gate-previews
python projects/shanghai/source/precise/chongming-lingxing-photo-right-gate/source/package_assets.py --raw /tmp/lingxing-right-gate/chongming-lingxing-photo-right-gate-raw.glb --lod /tmp/lingxing-right-gate/chongming-lingxing-photo-right-gate-lod.glb --native /tmp/lingxing-right-gate/chongming-lingxing-photo-right-gate.blend --out projects/shanghai/assets/models/candidates/chongming-lingxing-photo-right-gate --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/chongming-lingxing-photo-right-gate/source/verify_geometry.py --assets /tmp/lingxing-right-gate --out /tmp/lingxing-right-gate-geometry.json
```

原语与GLB序列化辅助代码来源见`source/HELPER_PROVENANCE.json`，主体门框、关闭门叶及验证条件独立编写。Blender保存重开核对模型几何，舞台不计入建筑。原创代码与几何MIT。
