# 淮海中路1469号历史花园立面

市房管局第二批2D007登记这处花园住宅。馆方历史页记主屋建于1921年，最初由怡和洋行使用。两幅馆方档案影像清楚显示花园面中央浅门廊、跨层窗列、水平线脚和台阶；屋面及两翼大部分被树木遮挡。本件据照片可辨的中段制作。2010和2011分别是照片公开、存档年份，精确拍摄日期未知。[馆方原片与文字](../../../source/precise/xuhui-huaihai-1469-garden-front/reference-review.json)

| 文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| 原始GLB | 326,128 | d59deed0396dd54816e865c01d4a2287628290f15f561cf5d3105cb24e3a7548 |
| 网页近景 | 125,324 | 19153dc47e380a246b658f3e8b75b777f4522d81ced2717a22b71f8f630702fc |
| 远景LOD | 71,380 | 816b32f3a9235022ed61fe894c03bff2c49d14d2a14a91e436459e171d3478b8 |
| Blender | 162,232 | 8fe65e498ef0965138645f3e6f559eb50c6db6e1b5201c7db543eda73f6d50ef |

近景4,656面，远景2,724面，Blender重开后逐材料和原始网格核对，共35个可编辑网格。三份GLB各通过102个射线探针，覆盖五组高横窗、两排柱身和柱间空隙、层间腰线、窗框、浅门廊与六级台阶。[原生重开](geometry-native.json) [探针及落点](surface-checks.json) [四档文件](../../../assets/models/candidates/xuhui-huaihai-1469-garden-front/manifest.json)

市区名录采用公开门牌的近似街区点。选择该点后可单独打开这段历史立面，模型朝向使用独立示意坐标。主图的历史登记符合既有条目格式，行走姿态、城市替换面、碰撞面均为空，源建筑和部件清单均为空。[历史地点合同](final-placement-contract.json) [45与169日期说明回归](historical-caption-review.json)

登记前在既有运行模块中试装该条目，核验网页两档绑定、零地面碰撞及零现场裁剪。[历史标记运行记录](marker-preflight.json)

独立页在桌面与390像素触屏分别完成正面、斜视和俯视六次操作，切换了两种细节，四种下载均与清单匹配。[独立查看页](../../../huaihai-1469-garden-front-history.html) [浏览与下载](viewer.json) [桌面正面](viewer-desktop-full-front.png) [手机斜视](viewer-mobile-full-oblique.png)

实际登记后共206处，城市运行时验证了0个替换面、0处地面碰撞。八套连续冻结的HTTP服务逐项核对168与169版本，共192次请求；原有大上海大戏院的1934—1937年摄影年代也已核回。[实际历史标记](historical-marker-raw206.json) · [192次HTTP](historical-layer-http.json)

最终206处站点的1,149项正式文件已按实际URL逐字节请求，共1,032,743,350字节。[全量HTTP回执](23169-all-http.json)

在205处的前一版本和新增后的206处版本，以同一街区视角核对了登记点。桌面和390像素触屏均从按区目录进入，现状图可见原有街区与登记牌。地点卡的“查看历史立面”打开单独的花园立面，正面的底层门廊、台阶和上下两排窗在两种屏宽均可辨认。查看器标注2010—2011年为影像资料收录年份，拍摄日期未详。实测切换近景和远景、关闭历史页后回到原地点卡。登记点在前后两版各连续三次地面检查均可通行，历史模型在现状地图的三角面与裁切均为零。[两版实测](final-map-31169/results.json) · [桌面原址](final-map-31169/desktop-location.png) · [手机历史近景](final-map-31169/mobile-archive-near.png) · [两代网页和文件绑定](final-map-31169/bound-inputs.json)
