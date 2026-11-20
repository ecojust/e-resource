# 外滩7号的两枚莲花标志

市房管局第二批2A004记为“大北电报局”，门牌中山东一路7号。2012年临江面的正面照与2025年斜照都可辨两枚独立金色标志。原始网页近景签入的2025年全幅照片仍可用于逐像素对照。[刊载名录和两张原照](../../../source/precise/bund07/revisions/front-pier-emblems/reference-review.json) · [定位和建模范围](../../../source/precise/bund07/revisions/front-pier-emblems/README.md)

对旧版两块石墙共测440次，命中原墙或突出0.10、0.17米的石材。新增两个镂空构件，分别有上部菱形孔、下部一对叶形孔和沿孔口收边的厚侧壁。完整模型新增1,760个三角面，合计279,636面；远景新增800面，合计111,788面。三档分别测试两个壁柱的24条射线，能够穿过实际孔洞再次命中原石墙；探测到金属带的位置则提前命中金色表面。[原版墙面](previous-pier-walls.json) · [三档72项、原材质与几何](geometry-comparison.json) · [项目原检验器](project-lod-verifier.json)

网页和原始近景仍各自嵌有原来的6,600,834字节照片。Blender重新打开后，保存了原网格、场景物件、材质及UV签名和打包照片签名，新增南、北壁柱标志可分别选择。五份目录的单体记录仍归入原有bund07，连续执行两次登记后文件相同。[四种资产](../../../source/precise/bund07/revisions/front-pier-emblems/manifest.json) · [原生保存后复核](native-reopen.json) · [五表试登记](registration-idempotent.json)

用同一光照和相机分别打开两版原生文件，正面全景可见左右壁柱与中间门额的相对位置。南侧近景能在三处孔洞内直接看见原有石缝。[近景前后对照](before-after.jpg) · [修订后正立面](output-bank-front.png) · [两机位、四张原图及 SHA-256](native-visual-comparison.json)

在前后两份149处目录中逐项核对，仅本栋的资产、面数和制作说明有变。其他148处的登记，以及本栋的地图位置、可步行入口、地块编号和边界均一致。外滩总表与两份单栋元数据同步指向新文件。[五份登记文件的具体字段](in-place-catalog-comparison.json)

原位修订在城市入口149处的前后版本分别完成桌面与手机实测。正面南壁柱同机位的最终截图中，穿孔莲花投影覆盖5,821像素，其中5,761像素的RGB最大通道差达到6。投影取自交付GLB的真实三角面。原有窗横档、石壁柱和三语门额在两次取景中仍可辨认。北侧莲花在这次南墩特写的画外，其两档造型另由同镜头原生渲染、可见面和旧墙射线核对。

[旧版同机位](main-map-before-desktop-detail.png) · [修订版同机位](main-map-after-desktop-detail.png) · [局部原像素对照](southern-pier-city-before-after.png) · [网格投影复核](real-map-geometry-pixels.json) · [两站四件下载](final-21k-preflight.json)
