# 崇明学宫泮池与登云桥

**本轮更新：**[进入独立模型室外漫游](../../../pan-pool.html#mode=model-walk)。支持键盘／触屏移动、转向和外围碰撞；场景未配准到城市原址，不包含室内、登楼或上桥，不增加40处城市漫游数量。

[独立交互预览](../../../pan-pool.html) · [模型与下载清单](../../../assets/models/candidates/chongming-pan-pool-bridge/manifest.json)

新增池体、水面、拱桥、24级台阶、石栏及简化石狮的独立外观候选模型。尚未地理配准、接入城市或建立可行走桥面碰撞，不增加已接入的40处建筑目录数量。

## 来源与限制

[崇明博物馆旧官网存档](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_1.htm)记载：泮池为半月形，东西11.6米、南北6.16米、深2.1米；登云桥为单孔石拱桥，长10.1米、宽2.5米、高3.1米，南北各12级台阶。1998年修缮时将池栏、桥阶及栏杆改为花岗石。原网页不随项目再分发，仅保存引用、事实摘记与字节哈希。

[Joshua Wickerham 的2005年照片](https://commons.wikimedia.org/wiki/File:Pan_pool_and_Ji_Gate_of_the_Chongming_Confucian_Temple.jpg)，采用 [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/)，原图未修改，见 references/pan-pool-2005.jpg。Commons页面和EXIF具体日期存在一天差异，保留记录，不将上传日期当作现场核验时间。照片仅作结构参照，没有嵌入模型；人物、植物、建筑背景没有被贴成桥体。

半椭圆池形、拱线、每级0.14米高度、0.28米进深、0.8米水位落差、平池底、石材色彩与栏杆雕花均为解释性估计。文献3.1米桥高的测量端点不明；模型不是绝对高程测绘。石狮仅保留简化的蹲坐轮廓，不作为雕塑精确复原；桥拱题字、兽纹、现场风化与沉积层未复原。完整来源事实与建模取值分开保存在 design-input.json。

与尊经阁相同，现有地图源要素覆盖整个博物馆院落；本模型不能替换整个源要素。需要院落内部可靠配准和分构件处理后再接入，保持原城市建筑、地面和水面不变。不代表2026年现状，也不代表全市河床或铺装已经补齐。

## 重建

从 projects/shanghai 目录运行；Python依赖见 source/requirements.txt，Blender使用4.3.2，gltfpack使用仓库 source/city/detail/tooling 的锁定版本。

```sh
python source/precise/chongming-pan-pool-bridge/source/build_model.py --out /tmp/pan-full
python source/precise/chongming-pan-pool-bridge/source/build_model.py --lod --out /tmp/pan-lod
blender --background -t 4 --python-exit-code 1 --python source/precise/chongming-pan-pool-bridge/source/build_native.py -- --raw /tmp/pan-full/chongming-pan-pool-bridge-raw.glb --out /tmp/pan.blend --previews /tmp/pan-previews
python source/precise/chongming-pan-pool-bridge/source/package_assets.py --raw /tmp/pan-full/chongming-pan-pool-bridge-raw.glb --lod /tmp/pan-lod/chongming-pan-pool-bridge-lod.glb --native /tmp/pan.blend --out assets/models/candidates/chongming-pan-pool-bridge --gltfpack source/city/detail/tooling/node_modules/.bin/gltfpack
python source/precise/chongming-pan-pool-bridge/source/verify_structure.py --model /tmp/pan-full/chongming-pan-pool-bridge-raw.glb --report /tmp/pan-structure.json
```

原生文件可用 source/check_native_geometry.py 在 Blender 中重新打开，并逐三角形对照原始GLB。

四件模型分别为原始GLB、压缩网页GLB、远景GLB、Blender原生文件，均小于100 MB。远景保留24级台阶与真实拱洞，仅降低曲线采样和雕刻近似细节。Blender展示地面、相机与灯光单独成组，不属于建筑构件或实测场地。预览将地面降低到池底以下，剖露池壁和桥台基础，不能理解为现场池体高出地面。

原创代码与几何 MIT，参考照片独立采用 CC BY-SA 2.0；公用代码来源见 source/HELPER_PROVENANCE.json。[验证与截图](../../../data/audit/pan-pool-v1/README.md)。
