# 雷士德医学研究院主楼

上海市第二批优秀历史建筑2B024登记为“雷氏德医学院”，地址北京西路1320号。静安区政府记录该址1号楼于2024年8月启用和睦家门诊。模型选择保护修缮后的主楼外观。建筑南、东、西面为花岗石，背面采用水刷石。正门由深红石套、宽踏步与铜灯组成，西门可见浅色窄门套、矩形门额、门级及另一对铜灯。[名称和各类门牌](../../../source/precise/jingan-lester-medical-research-institute/README.md) · [市历保中心与修缮设计团队的现状影像](https://www.thepaper.cn/newsDetail_forward_26833339)

完整近景和原始模型各72,156个三角面，简化远景23,188个。Blender重开后核对75个可编辑部件。三档GLB分别独立解码并复核南面每一条宽钢窗、中央门扇、窗间柱、复原铜灯和屋顶退台，合计93条首个交点射线。南门套、铜灯、黑钢窗格、窗下板和中塔门窗可分别编辑。[原生网格与编码校验](geometry-native.json) · [三档共93条射线](opening-rays.json) · [原生模型实图](jingan-lester-medical-research-institute-preview.png)

实名院址与航拍、绿地、北部凹口和周边四栋的地面关系共同识别w490437625与14-13719-6694的260号源。其原始地理属性还引用另一项4B006花园住宅及矛盾门牌，本次保留这项来源差异。近远两份实际原生网格分别核验该源全部由主楼接替，同组十处其他源的几何保持完整。最近其他原生建筑与裁剪边界相距2.64米；草坪、北庭、东西侧与两处门口分别核对地面通行性。默认视角以六个立面和塔顶部位核验周边遮挡。[各源、地面与原生网格](footprint-review.json) · [成品安置参数](final-placement-contract.json) · [两种屏幕高度的视线](overview-sightlines.json)

在上海项目目录下，根据来源收据取得冻结宏区文件，并使用空工作目录重新执行核验。

    python -B data/audit/lester-medical-research-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/lester-institute-review
    python -B data/audit/lester-medical-research-v1/check-openings.py --work "$WORK" --report /tmp/lester-institute-review/opening-rays.json
    python -B data/audit/lester-medical-research-v1/check-overview-sightlines.py --feature-table "$MACRO/feature-table.json.gz" --contract /tmp/lester-institute-review/final-placement-contract.json --report /tmp/lester-institute-review/overview-sightlines.json

独立页在1250×820与390×844两种视口各加载近、远两档。正面能看到南侧阶梯形门塔、中央红色石门套与每侧六列深色贯通窗。四件交付物的真实下载签名均匹配，四次截图完成，页面错误为零。[浏览器及下载](viewer.json) · [桌面完整景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [外观复核](visual-review.json)

正式城市目录从168处增至169处。两个实际HTTP服务返回的目录字节与各自冻结树一致，原有128个候选记录保持相同。[正式输入及SHA-256](production-snapshot.json) · [前后目录HTTP核对](predecessor-controls.json)

### 城市地图实测

第168处前代站和第169处交付站使用相同的北京西路镜头。前代能看见带灰色方格窗的原始体块，交付站的默认桌面和手机能辨认中央退台门塔，以及两边各六列贯通窗。手机点页面自带的“＋”后，门套、铜灯与楼面窗格仍可见。专项街景中的本楼灯牌遮到门洞下部，铜灯近图能分辨两边灯柱和台阶。西门专项街景被保留的相邻灰楼遮住，独立查看器和几何射线记录了西门细部。通过键盘搜索“雷氏德工学院”后，医学研究院模型及其裁剪均退出。再搜索“雷士德医学研究院”即返回同址。[前代同机位](final-map-24131/map-before.png) · [默认桌面](final-map-24131/main-desktop.png) · [默认手机](final-map-24131/main-mobile.png) · [正常放大](final-map-24131/mobile-public-zoom.png) · [正门细部](final-map-24131/bronze-lamp-pair.png)

地面共核对13处，包括临街草坪、北庭、东西翼、两处入口和五个邻楼。近景11个原始地块中仅260号源启用替换。独立页面、查看器、三档GLB与Blender文件的实际响应分别核对至既有四幅截图和四次保存下载。桌面首轮在截图后中断。手机首轮保存了默认截图，随后遇到测试脚本误用旧控件名，复测通过实际的页面按钮完成。[切换及地面记录](final-map-24131/interactions.json) · [独立页与两代HTTP](final-map-24131/pair-and-standalone-http.json) · [整站827项实取](final-map-24131/131-all-http.json) · [各次实测汇总](final-map-24131/measured-summary.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/7a4d9719918ed6ab93ad70c6fde67d5fd91a285e/projects/shanghai/index.html#landmark=jingan-lester-medical-research-institute&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
