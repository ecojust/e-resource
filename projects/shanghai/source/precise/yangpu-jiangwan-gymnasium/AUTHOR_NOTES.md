# 江湾体育馆历史主楼模型制作说明

本件是江湾体育中心内独立封闭体育馆，不是已交付的室外体育场，也不是游泳馆。以具名地图源1558（`adde8d71-bc6d-497a-a682-3bb158c1f160`）约束平面，采用东/北/上本地坐标，主入口朝西。原源外包约72.878×44.847米，与1934方案整体约82×46米不同；没有为凑82米向西扩建或侵占道路。原源15.15米是CMAB预测，不是测量高度。

作者实际查看了KIC运营站2011归档中的两张西门现代照片、2013泳馆照片背景中的独立体育馆、2024介绍中的两张高位全景、运营页面中的馆内照片，以及1934相关文字/透视/平面/正侧背立面。归档年份不是摄影日期；馆内图EXIF年份有矛盾，引用只用于可见的钢拱顶光和高窗构造。照片均只作研究，不用作贴图或随仓库分发。具体URL、日期差异和许可由同目录来源登记给出。

现代近照约束浅石西门的三个高竖窗、三个带圆孔栏板的挑台、三个深拱口；两侧采用真正有菱形孔的格门，中门保持更深的暗凹。暗凹后方的封闭面仅界定未制作的室内，不声称现场中门是实心门，也不宣称可以直通室内。门槛高0.13米为作者估计；没有把历史效果图中的大面积台阶移作现代确定构造。前台四塔、鼎和三大外拱属于室外体育场，未移植到体育馆。

弧顶是独立闭合金属壳，中央纵向天窗有真正的屋面开口、独立玻璃板和分格框，玻璃下面没有另藏不透光金属面。屋面曲率、金属立缝间距、天窗长度/宽度和分格均属作者估计，现代高位与馆内图仅约束其形态。天窗长度选约33.47米，约占主屋面61米的55%；2013照片背景体育馆中天窗可见段大约占屋面的半段，透视与前景遮挡不能用于精测，此比例是有界作者估计。原设计“八角小窗各十六孔”中的“八角”指形状，数量为每侧16；本模型作每侧16个八角高窗，低位窗门列及遮挡部位具体分配含估计。

主屋檐选12米，金属弧顶顶点20米，天窗框最高约20.17米；它们以历史20/12米方案作比例辅助，不当作今天的实测。西门主体墙16.4米、翼墙13.5米，盖板另高0.15米，挑台板中心6.05米、前伸1.02米均为模型选择。后立面和被树遮挡的长侧下部只做有界外观概括，与正门区别处理；没有镜像三拱门、旗帜、临时横幅、大雕灯或未见的高塔。

各作者组件分别闭合、绕序一致且正体积，未声称整馆经过布尔并集。对相接构件避免外表面共面：长侧墙端盖收在端墙内部，弧端墙顶接入屋面厚度，前附体盖板高于墙顶；高体多折返墙连续闭合。低位腰带和其他横饰按实际洞口裁断，避免横穿三拱门。格门真孔、挑台圆孔、挑台下凹和屋面天窗均有实际序列化射线核验。预览地面不是建筑资产；没有室内座席、球场底板、体育场、泳馆、全场绿地或邻楼。

## 重建

脚本位于`source/`，与`common/photo_architecture.py`和`model-parameters.json`保持相对位置。Python依赖见`source/requirements.txt`，本轮原生使用Blender4.3.2，打包使用gltfpack0.25。

```sh
python source/build_model.py --out /tmp/jiangwan-gym-build
python source/build_model.py --lod --out /tmp/jiangwan-gym-build
python source/verify_author.py --out /tmp/jiangwan-gym-build/author-geometry-checks.json
python source/verify_author.py --lod --out /tmp/jiangwan-gym-build/author-geometry-checks-lod.json
python source/verify_serialized.py --asset /tmp/jiangwan-gym-build/yangpu-jiangwan-gymnasium-raw.glb --probes /tmp/jiangwan-gym-build/surface-probes.json --out /tmp/jiangwan-gym-build/raw-rays.json
blender -b -t 2 -P source/build_native.py -- --raw /tmp/jiangwan-gym-build/yangpu-jiangwan-gymnasium-raw.glb --out /tmp/jiangwan-gym-build/yangpu-jiangwan-gymnasium.blend --previews /tmp/jiangwan-gym-native --views front,oblique,rear,roof,entrance,south,roofdetail --samples 12
python source/package_assets.py --raw /tmp/jiangwan-gym-build/yangpu-jiangwan-gymnasium-raw.glb --lod /tmp/jiangwan-gym-build/yangpu-jiangwan-gymnasium-lod.glb --native /tmp/jiangwan-gym-build/yangpu-jiangwan-gymnasium.blend --out /tmp/jiangwan-gym-assets --gltfpack /path/to/gltfpack
```

压缩网页版和远景版必须先用gltfpack解码，再运行实际射线及逐材质有方向FLOAT32三角等价检查；不能将扩展未解析的空网格当作通过。代码独立验证实际GLB是单场景、单恒等节点后才收集网格，原生另在实际保存后重新打开并核几何。

实际解码检查示例（远景版换成对应文件与`surface-probes-lod.json`）：

```sh
/path/to/gltfpack -i /tmp/jiangwan-gym-assets/yangpu-jiangwan-gymnasium-web.glb -o /tmp/jiangwan-gym-build/decoded-full.glb -noq -vnf -km -kn -ke
python source/verify_serialized.py --asset /tmp/jiangwan-gym-build/decoded-full.glb --source-asset /tmp/jiangwan-gym-assets/yangpu-jiangwan-gymnasium-web.glb --probes /tmp/jiangwan-gym-build/surface-probes.json --out /tmp/jiangwan-gym-build/full-rays.json
```

`--source-asset`明确绑定被解码的压缩源文件，避免gltfpack不保留顶层extras时误认模型；报告保留原件和解码件的SHA-256。完整网页版须与raw的逐材质有方向FLOAT32三角摘要一致，LOD则与未经压缩的LOD一致。

共用闭合棱柱、立面框架和GLB导出工具及通用保存/验证流程源于仓库MIT代码，详细来源见`source/HELPER_PROVENANCE.json`。本栋弧顶、天窗、映射轮廓、三窗挑台、真孔门和组合构造为新编。原创代码/几何按MIT提供，地图平面参考保留ODbL-1.0，文献和摄影保留其各自权利。
