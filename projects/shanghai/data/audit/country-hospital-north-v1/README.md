# 宏恩医院历史主楼北翼与中部门诊连接体

## 几何与原生工程

北翼长墙按约 35.4 × 14.6 米、中部连接体按约 10.5 × 18 米建模。入口凸出约 1.9 米。北立面与东端以修缮前照片为依据，院侧和连接体外墙的细部采用简化表达。具体年代、照片和覆盖范围见[参考记录](../../../source/precise/jingan-country-hospital-north-block/reference-review.json)。

同一次构建生成原始 GLB、网页 GLB、LOD 与可编辑 Blender 工程。原始和网页模型各有 38,208 个三角形，LOD 有 14,560 个。重新打开最终 .blend 后逐材质核对 97 个网格的有向三角面，并分别解压网页与 LOD 文件、逐面比较其导出输入。独立射线检查从三个成品文件逐一测试 36 条射线，覆盖入口、窗墙、东立面、屋面及庭院空区。[模型校验](geometry-native.json) · [108 条射线检查](surface-checks.json)

## 原生渲染与修正

第一轮预览显示窗台前伸过多，北墙与端墙的重合面在侧角产生暗条。终版收薄窗台、调整接缝并将入口饰线收至地面。下面三张图均来自重新打开的最终工程，使用 Cycles 48 采样及 Open Image Denoise CPU 滤波。斜视图可辨中部连接体向院内延伸、东墙窗组和女儿墙，入口近景可辨拱顶、灯具和四字院牌。[初版预览](preflight/initial-render.png) · [最终预览](jingan-country-hospital-north-block-preview.png) · [斜视](native-north-east.png) · [入口](native-entrance.png) · [补充机位脚本](render-inspection.py)

| 补充渲染 | SHA-256 |
| --- | --- |
| 东北斜视 | 4f9ff0f1c236499564c85ebc666a743e955d07693dadd437f32bcaecc11c2e5b |
| 入口近景 | acfc9b6155f7d480d80d2f79f87f2918684de89adb60ebf1592a12f732b08874 |

院牌文字按入口照片读取为「华东医院」。四个挤出字采用 Noto Serif CJK SC 的改名子集，牌面字形、笔画和色泽均为近似。工程包含可编辑的字形网格。字体和上游散列见[来源与版本](../../../source/precise/jingan-country-hospital-north-block/source/fonts/provenance.json)和[许可](../../../source/precise/jingan-country-hospital-north-block/source/fonts/OFL.txt)。

## 独立预览与主图配准

在桌面和 390 像素竖屏实际打开预览，逐档切换网页与远景模型。正视图可辨中央入口和两侧窗列。四个下载按钮取得的文件与清单大小、SHA256 均相同。初次测试期间补充了“顶升修缮前”的图注，两次打开的页面字节不同；图注定稿后已全项重跑。[最终预览检查](viewer.json) · [窄屏正视图](viewer-mobile-full.png) · [图注修改期间的检查](preflight/viewer-during-caption-update/viewer.json)

北翼模型在已有花园立面和相邻建筑之间新增单独入口。北横翼和中部连接体分别切入原始地图的 848 与 2764 号体块，两处开口按照各自原屋顶高度收边。三档模型与两个地图源的近远景逐三角面比对，相邻体块没有被裁掉。地面碰撞按两米以下的实际几何推导。全市现有 86 处入口，静安区 3 处。[裁剪、碰撞与相邻体块](placement-geometry.json) · [定位数据](final-placement-contract.json) · [目录增量核对](catalog-preservation.json)

在主图中，窄屏从静安区目录进入，桌面以近景和鸟瞰核对北翼、连接体和相邻建筑。正对北楼时，前方另栋的屋面遮住部分底层门洞。保留该栋后，完整入口、灯和院牌可在单体页观看。全市缩放下的 86 个灯牌均可通过命中测试，在密集排列中分别实点鼠标与触屏返回北翼。浏览器取得的四件模型文件及三份原地图资源均已核对字节。[主图实测](main-browser.json) · [画面复核](map-visual-review.json) · [北向近景](map-north-face.png) · [手机灯牌](map-beacons-mobile.png)

## GitHub 发布

资产提交 `ae55637ce1d7cbc4d21fd94934c8309aca1dcd09` 已推送 master。逐字节检查固定版本的主图、运行模块、目录、清单及四件下载，共 26 项通过。首次同时访问 master，有 13 项仍返回缓存中的旧字节。[固定版本的上海主图](https://raw.githack.com/ecojust/e-resource/ae55637ce1d7cbc4d21fd94934c8309aca1dcd09/projects/shanghai/index.html#landmark=jingan-country-hospital-north-block&mode=overview) · [固定版本公开核对](publication.json) · [master 首次核对](publication-master-initial.json)
