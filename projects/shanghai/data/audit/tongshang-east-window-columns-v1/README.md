# 外滩6号二层中央三窗贴柱核验

在中国通商银行既有模型的东立面，按2014、2025年的照片补建了三对细身石柱和方形柱头。两张照片都能辨认柱身与柱头轮廓，雕刻图案及实际尺寸仍属估计。2014年的阳台矮墙与2025年可见的玻璃挡板分别记入来源。原资产的六处位置只有两级平券套。[查证与原文件](../../../source/precise/bund06/revisions/east-window-columns/reference-review.json) · [六处旧网格断面](previous-jamb-profiles.json) · [照片对照](photos-and-v6.jpg) · [图像许可](image-credits.md)

原始、网页近景各100,735个三角面，远景45,663个。三档原有场景的世界坐标三角面和逐面材质按原顺序全部相同。新模型三个方向的外包围盒相同。两个近景保留原CC0照片的全部6,420,018字节，远景沿用V6的无照片材质。独立读取器分别从三档模型还原六个柱轴，检测每根柱身四个高度的左、中、右三条射线并检查柱头宽度。原有91,111个近景三角面和40,467个远景三角面均逐个核对。[几何、材质和射线报告](geometry-comparison.json) · [项目外滩LOD验证器](project-lod-verifier.json) · [四件下载清单](../../../source/precise/bund06/revisions/east-window-columns/manifest.json)

Blender 4.3.2重新打开原文件和修订文件。旧主体顶点、三角面、面材质、UV和图片保持一致，六根新增石柱均有独立可编辑网格。两幅图片使用同一视角和同一照明，能辨认原来平直的窗边、新增圆柱与檐下的小型柱头。[原生重开](native-reopen.json) · [同角度前后对照](before-after.jpg) · [修订后原图](output-jambs.png)

在隔离的登记预演中，既有地标表、外滩模型表、远景表及该楼的两个独立元数据文件均指向清单中的新件。三表保持原登记项数、顺序和其他各行，既有地图碰撞与定位沿用原值。重复执行登记写入后的文件SHA-256一致。正式主图切换和整站发布另行记录。[局部登记预演](registration-preview.json)

126处正式预演场景逐一读取412项输入共299,020,695字节，包含地标、目录、页面和模型下载。[全部HTTP记录](frozen-scene-http.json)

在前后两份126处目录中逐项核对，仅本栋的资产、面数和制作说明有变。其他125处的登记，以及本栋的地图位置、可步行入口、地块编号和边界均一致。外滩总表与两份单栋元数据同步指向新文件。[五份登记文件的具体字段](in-place-catalog-comparison.json)

在126处入口的地图上，通过 HTTP 实取带版本号的三份地图登记表，以及按 SHA-256 寻址的普通建筑总表、分区索引和替换表。共核对15个请求，返回字节与冻结清单一致。[逐次请求](metadata-cache-http.json) · [本次调整涉及的文件](runtime-input-changes.json)


## 主图同机位对照

外滩6号在两版主图中均由原有地标入口进入。126个地点的旧站实载91,111个三角面，修订站实载100,735个。两次使用相同的相机位置、俯仰、朝向和街面高度。三扇二楼弧顶窗的两侧现各有一根贴柱，六处柱帽均可辨。灯牌遮住最左一扇窗的下缘。[并排原图裁切](same-camera-window-comparison.png) · [旧版全幅](main-map-before-detail.png) · [修订版全幅](main-map-after-detail.png) · [实测目录、模型散列和相机](main-map-comparison.json)

主图实拍来自15082和15083；随后对17082与17083的正式目录分别实取近、远两件模型，登记散列与实拍版一致。[正式目录的网络核验](corrected-registry-and-web-assets.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 30 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/9f0888a873db1bc951d2ade3b45b4cd03e91be56/projects/shanghai/index.html#landmark=bund06&mode=walk) · [固定版本逐文件核对](publication.json)

首次在 master 检查 30 项时，有 8 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
