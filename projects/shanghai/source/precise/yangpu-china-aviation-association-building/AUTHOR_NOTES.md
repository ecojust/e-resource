# 飞机楼：作者几何说明

本楼的平面组合、曲面墙壳、开窗、筒拱、三重退台栏圈、双弧梯及东西门均为本轮新建；没有复用其他建筑网格。西侧半圆入口阶只保留建筑外部部分，不把阶体伸入两翼地板。通用封闭体、导出与校验辅助代码来源见 `source/HELPER_PROVENANCE.json`，保留原MIT许可。

作者实际查看2013 Commons斜俯视、2010 Commons西门原片，以及2022发布文章的顶视、两张前斜视、顶冠特写、东门阳台、馆外楼层牌和美篇东门正照，共9张。它们支持现存修缮后外形，不证明1935原状、现场测量或所有立面完整窗位。前翼两层主体的三道不等高窗带与圆塔第三层关系分开表达。机身两侧和后翼普通侧窗只是根据可见类别和两层关系推定的间距；龙纹、云纹及航空徽记仅作可辨轮廓简化，文字铭文不臆写。

坐标采用本地ENU米（x东/y北/z上），导出GLB为x东/y上/z南，heading0。地图锚点来自独立mapping审查，粗OSM不对称轮廓根据顶照规整；所有选用尺寸/高度均为估计。顶照复核后圆塔中心采用前翼进深中线偏西约1.2米的有界估计，西侧前凸约2.4米；粗OSM西凸弧不作为精确塔心。1522平方米是文字总建筑面积，未作为占地面积。地下、室内房间、医院邻楼、白棚、地面铺装、树木和夜间灯带不并入。

墙面用一个沿凹多边形周界的闭合薄壳与真实几何窗洞制作，框和玻璃有内退；低筒拱、屋顶平台和圆亭盖均封闭。三个台栏均为真开孔几何。每个构件检查FLOAT32闭合边、绕序、正体积与非零三角形。较高前翼与低筒拱、较低尾翼与筒拱的两端高差补有沿拱线封墙；屋面板侧边退入墙厚内；各灰色平屋面和环台的表面再低于结构墙顶及栏基4厘米（估计），由窄石材泛水台衔接，消除浏览器中可见的屋面顶面/墙壳顶盖共面碎斑。六条最终raw外向射线针对接缝和檐部，证明这些点首命中正确石墙；另扫描全部同高度向上灰屋面与石材顶盖并确认交集为零，用八条垂直射线核实石台与下沉灰面的接触。检查不声称覆盖整栋所有可能射线或全部方向的布尔并集。

Blender内建筑网格为可编辑几何，场景预览地面、相机和灯单列预览集合，不属于导出的建筑。8图在同一建筑几何保存前渲染，随后保存并实际重开`.blend`核对建筑几何摘要一致；这不是声称8图均在保存后重新渲染。

## 可移植重建

在任意独立目录复制本目录，安装 `source/requirements.txt`（Python3.11，numpy2.3.5、Shapely2.1.2、trimesh4.9.0），运行：

```sh
python3 -B source/build_model.py --out build
python3 -B source/build_model.py --out build --lod
python3 -B source/verify_author.py --out build/author-geometry-checks.json
python3 -B source/verify_author.py --lod --out build/author-geometry-checks-lod.json
python3 -B source/verify_junctions.py --raw build/yangpu-china-aviation-association-building-raw.glb --out build/junction-rays.json
python3 -B source/verify_roof_caps.py --asset build/yangpu-china-aviation-association-building-raw.glb --out build/roof-cap-checks.json
blender -b -t 4 -P source/build_native.py -- --raw build/yangpu-china-aviation-association-building-raw.glb --out native/yangpu-china-aviation-association-building.blend --previews native --samples 16
python3 -B source/package_assets.py --raw build/yangpu-china-aviation-association-building-raw.glb --lod build/yangpu-china-aviation-association-building-lod.glb --native native/yangpu-china-aviation-association-building.blend --out assets --gltfpack /absolute/path/to/gltfpack
```

打包使用gltfpack0.25的meshopt压缩和`-noq -vnf -km -kn -ke`，不简化成改变可见细节的自动LOD；LOD由原始参数另建，减少弧采样和微细格栅，保留大形、入口、筒拱和开孔台栏。每文件严格小于100MB。GLB没有嵌入照片、外部贴图或外部buffer。
