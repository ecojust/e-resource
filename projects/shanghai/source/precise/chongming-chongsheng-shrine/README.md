# 崇明学宫崇圣祠正殿：文献参照外观候选

[独立预览与模型室外漫游](../../../chongsheng-shrine.html) · [资产清单](../../../assets/models/candidates/chongming-chongsheng-shrine/manifest.json) · [检查记录](../../../data/audit/chongsheng-shrine-v1/README.md)

依据崇明县博物馆旧官网“崇圣祠”一节，新增三开间正殿候选，含单檐歇山曲面屋顶、平行瓦垄与瓦当、檐下椽条、简化斗栱、柱脚、十二扇格门、内退暗面及入口三级台阶。尚无可核验的该单体照片，不能把门窗、色彩和雕饰当作真实现场细节。

## 来源与限制

[博物馆原文存档](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_2.htm)第5节记载：三楹，1991年修复正殿；单檐歇山式砖木斗栱建筑，面阔12.5米、进深11.75米、高11米；另列占地169.62平方米。2026-10-29读取，原始响应SHA256及设计解释见[design-input.json](design-input.json)，不再分发整篇网页。

长宽乘积146.875平方米与文献面积不符，模型沿用长宽，没有为凑面积放大。文献未指明尺寸对应墙线、柱线或檐线，本模型把长宽解释为基座边界；最高点11米为约束，不构成实测精度。屋檐外挑、檐高、曲线、三开间等分、门扇数量与格数、构件截面、斗栱层次、台阶、侧后封墙及颜色均为估计。屋顶实际外包宽约14.60米、深约13.85米（含估计脊端）。没有照片像素贴图或实测PBR。

未复原历史前门、室内、匾额文字、精确雕刻及院落。未获得单栋地图轮廓与配准，模型不替换城市建筑、不计入40处原址漫游；独立室外漫游仅围绕本候选，不是城市原址或室内漫游。不声称2026年现状或逐栋复原验收完成。

## 重建

从仓库根目录运行（Python依赖固定在`source/requirements.txt`；本次Blender版本见检查记录）：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-chongsheng-shrine/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-chongsheng-shrine/source/build_model.py --out /tmp/chongsheng
python projects/shanghai/source/precise/chongming-chongsheng-shrine/source/build_model.py --out /tmp/chongsheng --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-chongsheng-shrine/source/build_native.py -- --raw /tmp/chongsheng/chongming-chongsheng-shrine-raw.glb --out /tmp/chongsheng/chongming-chongsheng-shrine.blend --previews /tmp/chongsheng-previews
python projects/shanghai/source/precise/chongming-chongsheng-shrine/source/package_assets.py --raw /tmp/chongsheng/chongming-chongsheng-shrine-raw.glb --lod /tmp/chongsheng/chongming-chongsheng-shrine-lod.glb --native /tmp/chongsheng/chongming-chongsheng-shrine.blend --out projects/shanghai/assets/models/candidates/chongming-chongsheng-shrine --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/chongming-chongsheng-shrine/source/verify_geometry.py --assets /tmp/chongsheng --out /tmp/chongsheng-geometry.json
```

辅助几何取自同仓库MIT大成殿源码，来源与哈希见`source/HELPER_PROVENANCE.json`；平面与单檐屋顶独立编写。Blender文件含可编辑网格、预览舞台及相机，保存后重开核对模型几何哈希；原生字节不承诺确定性。原创代码与几何MIT。
