# 上海孙中山故居主楼外观候选

**漫游接入更新：**已开放[原址室外第三人称漫游](../../../index.html#landmark=huangpu-sun-yatsen-residence&mode=walk)，起点、保守建筑碰撞与近远景切换记录见[接入核验](../../../data/audit/precise-buildings-v22/huangpu-sun-yatsen-residence/README.md)。下列初次建模记录中的“未接入”描述属于交付时状态；尺寸和未见构造仍为估计，不代表整栋历史复原完成。

[独立预览](../../../sun-yatsen-residence.html) · [模型下载](../../../assets/models/candidates/huangpu-sun-yatsen-residence/manifest.json) · [验收记录](../../../data/audit/sun-yatsen-residence-v1/README.md)

主楼四孔拱廊为真实开口，后方有退进门窗；上层包含两扇拱窗与西侧长窗、百叶通风口、交接屋面、逐片瓦、烟囱和六级入口台阶。原生Blender文件含可编辑网格、嵌入的原创卵石墙PBR和独立预览舞台。完整模型81,088面，远景8,084面。

本批为外观候选。已识别冻结地图中独立的主楼3433号对象，但没有替换城市网格、碰撞或增加漫游目录，不计入1,796,419个要素的逐栋复原完成量。花园、邻近文物馆及其他邻楼、室内、准确匾额文字、当前未见的侧后窗洞均未复原。侧后立面为简化封闭墙，照片不能支持其完整性。

## 来源与估计

[区志原文存档](https://web.archive.org/web/20220627050101id_/http://www.shtong.gov.cn/newsite/node2/node4/node2249/luwan/node36738/node36743/node62688/userobject1ai21722.html)记载香山路7号、两层、坐北朝南、灰色卵石墙、洋红色鸡心瓦，占地1,013平方米、建筑面积452平方米。只引用事实，未再分发原网页。[设计输入](design-input.json)区分文献事实和估计。

建筑面积没有直接换算为实测墙线；房间、门廊及附属空间的面积口径尚不明确。模型主体17.6×16.4米、主脊11.7米、烟囱最高约12.975米，全部为地图轮廓和照片引导的估计。屋顶交接、瓦片、檐口、窗格细分、隐蔽构造、烟囱和六级台阶均不是测绘成果。2015/2017正面照片及2020航拍用于外观判断，不声称2026年现状。

[地图输入](geometry-input.json)冻结OSM `w206603275@9` 对应源UUID `9bbed57b-ae4b-4abc-be77-0b5444bf0a9a`、宏块 `14-13719-6695`、localId 3433。原数据推定20.45米高，与文献两层住宅不符，未采用该高度建模。锚点为源多边形质心，朝向取边线；源多边形不是实测墙线。地图资料归OpenStreetMap贡献者，采用[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/)。

## 照片署名

以下Commons文件原样分发，未编辑、未采样或嵌入模型纹理。[登记文件](public-photo-register.json)含原始元数据、下载URL、作者、许可、字节与SHA-256。

| 文件 | 作者、拍摄日期 | 许可 |
|---|---|---|
| [2017年正面](https://commons.wikimedia.org/?curid=65029966) | ScareCriterion12，2017-12-23 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| [2015年正面](https://commons.wikimedia.org/?curid=41106153) | Fayhoo，2015-06-13 | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| [2020年航拍](https://commons.wikimedia.org/?curid=86610688) | Legolas1024，2020-02-04 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |

原创几何、代码及程序生成材质采用MIT；照片保留各自许可。几何辅助库来自同仓库巴金旧居；程序材质改用本楼的随机种子和灰色调，见[辅助代码来源](source/HELPER_PROVENANCE.json)。没有把巴金整楼缩放为本楼。

## 重建

从仓库根目录运行；Python依赖固定在`source/requirements.txt`，Blender 4.3.2，gltfpack 1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/huangpu-sun-yatsen-residence/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/huangpu-sun-yatsen-residence/source/generate_material.py --output projects/shanghai/source/precise/huangpu-sun-yatsen-residence/textures
python projects/shanghai/source/precise/huangpu-sun-yatsen-residence/source/build_model.py --out /tmp/sun-house
python projects/shanghai/source/precise/huangpu-sun-yatsen-residence/source/build_model.py --out /tmp/sun-house --lod
blender -b -t 4 --python-exit-code 1 --python projects/shanghai/source/precise/huangpu-sun-yatsen-residence/source/build_native.py -- --raw /tmp/sun-house/huangpu-sun-yatsen-residence-raw.glb --out /tmp/sun-house/huangpu-sun-yatsen-residence.blend --previews /tmp/sun-house/review
python projects/shanghai/source/precise/huangpu-sun-yatsen-residence/source/package_assets.py --raw /tmp/sun-house/huangpu-sun-yatsen-residence-raw.glb --lod /tmp/sun-house/huangpu-sun-yatsen-residence-lod.glb --native /tmp/sun-house/huangpu-sun-yatsen-residence.blend --out /tmp/sun-house/assets --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

GLB坐标为锚点局部East/Up/-North，朝向已烘焙，不能再次加同一旋转。墙纹理按0.4米周期映射；GLB的V轴向下，未导出TANGENT，由加载器处理法线贴图约定。网页打包保留浮点UV和坐标。Blender文件字节不保证确定性，原始/远景GLB及程序材质可确定性重建；原生验收比较保存重开后的真实网格。
