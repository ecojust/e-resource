# 上海鲁迅故居正立面与院门候选

**本轮更新：**[进入独立模型室外漫游](../../../luxun-residence.html#mode=model-walk)。支持键盘／触屏移动、转向和外围碰撞；场景未配准到城市原址，不包含室内、登楼或上桥，不增加40处城市漫游数量。

[独立预览](../../../luxun-residence.html) · [模型清单与下载](../../../assets/models/candidates/hongkou-luxun-residence-facade/manifest.json) · [验证记录](../../../data/audit/luxun-residence-facade-v1/README.md)

本批制作山阴路132弄9号的**正立面与院门构件**：逐块跑马砖、拱形入口及退进门扇、二层六扇分格窗（右两扇开启）、三层阳台门和两侧窗、弧角钢栏杆、双托架、上部阶梯饰块、凹槽门柱、扇形与V形铁艺。完整模型33,880个三角面，远景7,348面。原生Blender文件可编辑，内嵌原创石质PBR；预览地面、灯光、相机属于单独的展示集合。

这不是整栋住宅的完成模型。未制作屋顶、侧后立面、室内、花圃植物及准确匾额书法。构件背面仅显示墙厚和门窗背侧，不是住宅后立面。没有城市地图替换或原址漫游；独立模型场景的外围碰撞已另行加入，不计入1,796,419个渲染要素的逐栋复原完成量。

## 依据与估计

[上海鲁迅纪念馆网页存档](https://web.archive.org/web/20160607083913id_/http://www.luxunmuseum.com/html/201501/b8b4963b21f645d8ad7f7e38d69dd2d8.html)记载地址、三层红砖红瓦新式里弄、占地78平方米、建筑面积222.72平方米。准确来源URL与下载内容哈希见[设计输入](design-input.json)。仅引用事实，未再分发该网页或其图片。面积口径不能直接换算成墙线、开间或层高。

立面宽5.5米、檐口10.1米、墙厚0.30米、院门前移2.5米，以及门窗、砖、栏杆、托架、门柱、纹理尺度和颜色，**全部为照片引导的估计**，不作测绘值。正面照片有透视和植物遮挡，底层左窗和入口细分只能简化。模型参照2010、2011年外观，不代表2026年现状。未在未见屋顶上推造红瓦几何。

[地图上下文](map-context.json)保留查询地址、响应哈希及相关OSM对象：Wikipedia坐标落在标为34–36号的OSM `w1349147490@1` 上，不能作为9号故居的替换对象；`node9907365281` 的故居POI也不能单独确认墙线。本模型采用未配准的局部坐标，`anchor`与`source_owner`均为空。地图上下文归OpenStreetMap贡献者，许可[ODbL1.0](https://opendatacommons.org/licenses/odbl/1-0/)。

## 照片与许可

| 参考照片 | 作者、拍摄日期 | 许可 |
|---|---|---|
| [全正面](https://commons.wikimedia.org/?curid=17254062) | Gisling，2011-10-30 | [CC BY-SA3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| [入口近景](https://commons.wikimedia.org/?curid=62127465) | Zhou Guanhuai，2010-07-28 | [CC BY-SA4.0](https://creativecommons.org/licenses/by-sa/4.0/) |

两张照片原样分发，未编辑、未采样为模型纹理；[登记文件](public-photo-register.json)记录原始元数据、作者、许可、大小和SHA-256。2010照片于2017年上传，建模依据的拍摄年份是2010年。

原创几何、程序和程序生成石材纹理采用MIT。通用几何导出器沿用同仓库孙中山故居的MIT辅助代码，未缩放或复制其整楼几何；[来源记录](source/HELPER_PROVENANCE.json)绑定辅助库哈希。石材为原创通用纹理，随机种子13209，不是故居表面扫描。

## 重建与检查

从仓库根目录运行；Python依赖固定于`source/requirements.txt`，使用Blender4.3.2、gltfpack1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/hongkou-luxun-residence-facade/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/hongkou-luxun-residence-facade/source/build_model.py --out /tmp/luxun
python projects/shanghai/source/precise/hongkou-luxun-residence-facade/source/build_model.py --out /tmp/luxun --lod
blender -b -t 4 --python-exit-code 1 --python projects/shanghai/source/precise/hongkou-luxun-residence-facade/source/build_native.py -- --raw /tmp/luxun/hongkou-luxun-residence-facade-raw.glb --out /tmp/luxun/hongkou-luxun-residence-facade.blend --previews /tmp/luxun/review
python projects/shanghai/source/precise/hongkou-luxun-residence-facade/source/package_assets.py --raw /tmp/luxun/hongkou-luxun-residence-facade-raw.glb --lod /tmp/luxun/hongkou-luxun-residence-facade-lod.glb --native /tmp/luxun/hongkou-luxun-residence-facade.blend --out /tmp/luxun/assets --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

材质可用`source/generate_material.py --output /tmp/luxun-textures`独立重建并逐字节对比。原始/远景GLB与PNG可确定性重建；Blender文件只要求保存重开后的真实几何、UV和贴图一致，不要求文件字节确定性。

源坐标为右/后/上，GLB为右/上/前，不声称地理方位。石材按0.4米周期映射，不导出TANGENT；网页打包保留浮点坐标和UV。Blender的V翻转与网页的法线约定已分别检查。
