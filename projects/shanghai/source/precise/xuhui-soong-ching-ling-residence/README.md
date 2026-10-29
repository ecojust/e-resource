# 上海宋庆龄故居主楼外观候选

[独立预览](../../../soong-residence.html) · [模型下载清单](../../../assets/models/candidates/xuhui-soong-ching-ling-residence/manifest.json) · [验证记录](../../../data/audit/soong-residence-v1/README.md)

本批制作主楼外观候选：曲面四坡屋顶、逐片筒瓦、三扇有真实屋面切口的半圆老虎窗、曲线阳台、分格玻璃与百叶、柱廊、窗台装饰、烟囱和入口门廊。完整模型198,532个三角面，远景17,328面；提供原始GLB、网页压缩模型和可编辑Blender文件。墙面采用原创程序生成的浅色细颗粒PBR，未把照片贴到模型上。

本批不是测绘复原。建筑尺寸、弧度、细分、颜色和隐藏构造均为估计。侧后未见部分简化为封闭墙；入口门廊形态参照2016照片，但其置于模型后侧中央的位置和相对方位也属估计，未由平面图验证。附楼、游客中心、院墙、花园、室内及精确历史铁艺标记均未复原。未接入城市漫游，不计入1,796,419个渲染要素的逐栋复原完成量。

## 依据与尺度

[徐汇区志存档](https://web.archive.org/web/20210611135001id_/http://www.shtong.gov.cn/Newsite/node2/node4/node2249/xuhui/node38753/node38805/node63538/userobject1ai24027.html)记载：淮海中路1843号，主楼始建于民国9年，建筑面积700平方米，为船形两层白墙楼房，褐红色瓦带弧形屋面，二楼朝南有半圆形大阳台，占地4300余平方米。网页为GB18030编码，仅引用事实，不分发原网页及图片；URL和响应哈希见[设计输入](design-input.json)。

模型主体22×14米、檐高7.7米、主脊11米、通风管最高13.28米，均是照片比例引导的估计。文献建筑面积未用来直接推算测量墙线，也不把700平方米称作主楼占地。曲率函数、瓦尺寸、百叶间距、门廊位置、栏杆纹样、楼板厚度、烟囱尺寸和窗格数均不作实测值。参照2013、2016、2019年照片，不声称2026年现状。

[地图上下文](map-context.json)记录OSM院落`w490214455@6`及冻结宏块`14-13718-6695`相交的4个建筑记录，其中有独立游客中心。现有小轮廓和推定高度不能可靠确认为主楼，没有采用其20–25米高度或用整院落替换单栋。`anchor`、`source_owner`和`source_local_id`均为空；模型使用局部坐标，不声称地理朝向已配准。地图上下文归OpenStreetMap贡献者（ODbL1.0）及各冻结记录所列来源，仅用于身份筛查，未把源轮廓挤出为本模型。

## 照片署名

| 参考照片 | 作者、拍摄时间 | 许可 |
|---|---|---|
| [2019花园侧全景](https://commons.wikimedia.org/?curid=144856261) | Windmemories，2019-10-27 | [CC BY-SA4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| [2013阳台及窗台细节](https://commons.wikimedia.org/?curid=35823456) | Jpbowen，2013-09-28 | [CC BY-SA4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| [2016入口门廊](https://commons.wikimedia.org/?curid=48668898) | SSYoung，2016-05-08 | [CC BY-SA4.0](https://creativecommons.org/licenses/by-sa/4.0/) |

三张原图保持原字节分发，未编辑或采样进纹理。[登记文件](public-photo-register.json)包含许可、作者、拍摄时间、原始URL、大小和SHA-256。照片中的树木、人物及其他建筑不属于本模型。

原创几何、程序及程序材质采用MIT。通用几何导出器沿用同仓库鲁迅故居构件模型的辅助库；曲面屋顶和主楼布局为本批编写，不是另一栋整楼的缩放。材质算法沿用已有MIT程序，改为浅色颗粒和随机种子18431920，属于通用估计材质，不是现场表面扫描；[辅助代码来源](source/HELPER_PROVENANCE.json)记录复用范围。

## 重建

从仓库根目录运行。Python依赖固定于`source/requirements.txt`，使用Blender4.3.2及gltfpack1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/xuhui-soong-ching-ling-residence/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/xuhui-soong-ching-ling-residence/source/build_model.py --out /tmp/soong
python projects/shanghai/source/precise/xuhui-soong-ching-ling-residence/source/build_model.py --out /tmp/soong --lod
blender -b -t 4 --python-exit-code 1 --python projects/shanghai/source/precise/xuhui-soong-ching-ling-residence/source/build_native.py -- --raw /tmp/soong/xuhui-soong-ching-ling-residence-raw.glb --out /tmp/soong/xuhui-soong-ching-ling-residence.blend --previews /tmp/soong/review
python projects/shanghai/source/precise/xuhui-soong-ching-ling-residence/source/package_assets.py --raw /tmp/soong/xuhui-soong-ching-ling-residence-raw.glb --lod /tmp/soong/xuhui-soong-ching-ling-residence-lod.glb --native /tmp/soong/xuhui-soong-ching-ling-residence.blend --out /tmp/soong/assets --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

`source/generate_material.py --output /tmp/soong-textures`可独立重建PNG。原始/远景GLB及贴图可确定性重建；Blender字节不要求确定性，以保存重开后的网格、UV和打包图片为验收依据。展示灯光、相机和中性地面放在单独集合中，不属于建筑或测量地形。

源几何轴为右/后/上，GLB为右/上/前。墙面纹理按0.4米周期映射，无TANGENT，保留浮点UV；Blender与网页的V轴/法线约定已分别检查。
