# 崇明学宫尊经阁：独立外观候选模型

**本轮更新：**[进入独立模型室外漫游](../../../zunjing-pavilion.html#mode=model-walk)。支持键盘／触屏移动、转向和外围碰撞；场景未配准到城市原址，不包含室内、登楼或上桥，不增加40处城市漫游数量。

[打开交互预览](../../../zunjing-pavilion.html) · [资源清单](../../../assets/models/candidates/chongming-zunjing-pavilion/manifest.json)

依据2005年公开照片制作的可编辑外观模型，尚未地理配准，未接入城市替换或室内漫游；独立模型场景的外围碰撞已另行加入。现有城市精细建筑目录仍为40项，本模型不计入已完成接入数量。

## 证据和范围

- 原始照片：[Joshua Wickerham，Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Zunjing_Pavilion_of_the_Chongming_Confucian_Temple.jpg)，[CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/)。原图保存在 references/zunjing-2005.jpg，未修改；元数据与哈希见 public-photo-register.json。
- 尺寸：[崇明博物馆旧官网存档](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_2.htm)。台基18.65×14.4米，底层18×13.45米，上层13.8×9.25米。网页记载底层高5米、二层高7.5米，但高度端点不明，不能据此断言总高12.5米。模型最高点约7.93米属于解释性估计。
- 南立面门窗分组、双层灰瓦屋顶、红柱白墙、两块匾额参考照片。原图左端被裁切；侧后面、屋顶隐藏结构、雕刻、脊兽、精确曲率与色彩为估算。字形使用 Noto Serif CJK 子集，并非对实物书法的复刻。历史展览牌不代表当前展陈。
- 窗格采用真实几何开口及内侧暗色遮挡，模型没有嵌入照片纹理。不含可信室内、测绘高程、历史原貌或2026年现状认证。
- 原始地物 UUID 128f4cb0-fcdf-4948-8729-d812245dc745（OSM way 413345693）覆盖整个博物馆院落，不能直接用尊经阁替换。原地物存于 museum-source-feature.geojson（OpenStreetMap/Overture 来源，ODbL）；具体阻塞和探索性坐标见 registration-status.json。需要先区分院落各殿建筑并验证位置。

## 资源与重建

assets/models/candidates/chongming-zunjing-pavilion 包含原始 GLB、Meshopt 网页 GLB、远景 GLB、Blender 原生文件和 SHA-256 清单。每个文件小于100 MB。Blender 文件的预览地面、灯光与相机位于独立集合；预览地面不是实测场地。

在 projects/shanghai 目录执行（Python依赖见 source/requirements.txt；原生文件需要 Blender 4.3，压缩工具使用 source/city/detail/tooling 锁定版本）：

```sh
python source/precise/chongming-zunjing-pavilion/source/build_model.py --out /tmp/zunjing-full
python source/precise/chongming-zunjing-pavilion/source/build_model.py --lod --out /tmp/zunjing-lod
blender --background -t 4 --python-exit-code 1 --python source/precise/chongming-zunjing-pavilion/source/build_native.py -- --raw /tmp/zunjing-full/chongming-zunjing-pavilion-raw.glb --out /tmp/zunjing.blend --previews /tmp/zunjing-previews
python source/precise/chongming-zunjing-pavilion/source/package_assets.py --raw /tmp/zunjing-full/chongming-zunjing-pavilion-raw.glb --lod /tmp/zunjing-lod/chongming-zunjing-pavilion-lod.glb --native /tmp/zunjing.blend --out assets/models/candidates/chongming-zunjing-pavilion --gltfpack source/city/detail/tooling/node_modules/.bin/gltfpack
```

代码与原创几何采用 MIT；字体采用 SIL OFL，见 source/FONT-LICENSE.txt。参考照片保留独立 CC BY-SA 许可和署名。公用建模代码来源见 source/HELPER_PROVENANCE.json。[验证记录与原生渲染](../../../data/audit/zunjing-pavilion-v1/README.md)。
