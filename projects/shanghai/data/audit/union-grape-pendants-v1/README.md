# 外滩3号东北切角门的一对葡萄石雕

2013年12月29日的全门图片可同时定位两件垂饰，近物图片可复核叶结、端珠、双斜带及果粒。市房管局名录为二批2A002，门牌与已有外滩3号原生入口对应。[原照与拍摄者](../../../source/precise/bund03/revisions/northeast-grape-pendants/reference-review.json) · [制作与尺度](../../../source/precise/bund03/revisions/northeast-grape-pendants/README.md)

对原始近景的880个射线采样点只读出原有门券旁的平面、角石、线脚和分缝。制作时，最外侧卷枝末端最初被既有角石挡住。重新沿石面放置卷枝的外半段，在三档交付件中从正面均可碰到四颗端珠。每档另覆盖双叶、两条斜带、果粒和下垂叶尖，共54个新旧第一交点对照。[旧门采样](previous-entrance-profiles.json) · [新旧三档逐面与可见面核对](geometry-comparison.json)

完整新增11,784面，远景新增4,544面。新原始和网页近景均184,185面，远景75,078面。逐份解压后与旧档比对，旧172,401个近景三角面、70,534个远景三角面及各自材质索引、二进制前缀、资产版权字段和模型边界均一致。Blender重新打开检查旧网格坐标、面环、材质槽、UV和变换，新加的两个网格可各自选取。[四件成品](../../../source/precise/bund03/revisions/northeast-grape-pendants/manifest.json) · [Blender复开](native-reopen.json) · [项目几何核验](project-lod-verifier.json)

在五份实际目录的独立副本中试登记，现有目的地仍为bund03，原导航、地块、所有者及其他外滩建筑逐项相同。再次运行登记脚本，五个文件的字节均无变化。[登记检验](registration-idempotent.json)

在相同光照和机位下分别重开修订前后的Blender原件。正面全门图可见两个垂饰分列门券两侧，近照可辨上部卷结、左右端珠、两条斜带和下方果粒、叶尖。果粒的尺寸及起伏按单张近照估计，石面风化程度未据图定量。[同机位前后](before-after.jpg) · [全门](output-northeast-entrance.png) · [细部](output-east-relief.png) · [四张原生渲染指纹](native-visual-comparison.json)

在前后两份146处目录中逐项核对，仅本栋的资产、面数和制作说明有变。其他145处的登记，以及本栋的地图位置、可步行入口、地块编号和边界均一致。外滩总表与两份单栋元数据同步指向新文件。[五份登记文件的具体字段](in-place-catalog-comparison.json)

前后两版城市地图分别从21104、21105打开原来的外滩3号入口。850×650桌面和390×844手机都实际加载近景，旧版172,401面，新版184,185面。两份候选目录均为146处，SHA-256相同，各自的外滩清单和网页GLB也与HTTP签名吻合。两版桌面默认视角均可见临街窗墙，手机默认视角的一列周边灯牌盖住部分立面，常规缩放下难以看清单件石雕。[前态实测](main-map-before.json) · [后态实测](main-map-after.json) · [新版桌面](main-map-after-desktop-default.png) · [新版手机](main-map-after-mobile-default.png) · [两端HTTP与四个文件的签名](104-105-final-21k-http.json)

在相同的桌面街景机位，东侧券脚原为平石面。新版可见垂饰顶端两侧卷枝和端珠、中间斜带、下部果粒与叶尖。实际截图内东侧石雕外接范围为80×124像素，原始新增三角面投影覆盖3,498个像素。对比前后两图，其中3,000个像素至少有一个RGB通道相差6级，投影之外只有9个像素达到同一门槛。此近照只框入东侧一件，西侧可在上方的原生全门图中对照。[东券脚原尺寸截图裁切，左旧右新](east-jamb-map-comparison.png) · [旧版地图原图](main-map-before-desktop-detail.png) · [新版地图原图](main-map-after-desktop-detail.png) · [逐三角投影结果](real-map-geometry-pixels.json) · [复算程序](compare-map-detail.py)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 30 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/1686fde1fc662f2cd6ece7675318009edf4ab2d9/projects/shanghai/index.html#landmark=bund03&mode=walk) · [固定版本逐文件核对](publication.json)

首次在 master 检查 30 项时，有 11 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
