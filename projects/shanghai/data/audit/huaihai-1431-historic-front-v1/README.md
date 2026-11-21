# 淮海中路1431号巴塞住宅历史花园立面

全景409和近景410均出自里昂 Virtual Shanghai 登记的私人收藏，目录估年1920至1939年。1921年建成的住宅在这两幅照片中可辨出中央半圆柱廊、上下层窗列和花园台阶。全景与后来文章转载影像的归一亮度相关为0.9999。雪景提供了单独视角，能辨认两座瓦顶、阁楼窗及两端低附房。照片拍摄者和原建筑绝对尺寸待考。[原始出处与来源日期](../../../source/precise/xuhui-huaihai-1431-historic-garden-front/reference-review.json) [同幅与独立影像对照](photo-correspondence.json)

在900×609的雪景图上选取14个可辨位置，对照屋尖、两翼檐口、窗台和廊柱上下端。用独立的水平、竖直比例作正面近似，均方根差分别为10.97和4.02像素。照片有透视与进深差异，模型的绝对尺寸仍是估计。[逐点坐标及残差](front-proportion-review.json)

近景 43,904 个三角面，远景 24,328 个。原生 Blender 含 74 个可编辑网格，重开后逐材料核对三角面。两档网页模型均经 meshopt 实解码，与各自压缩前源几何逐材料相符。[原生重开与编码检查](geometry-native.json) [原生渲染](<xuhui-huaihai-1431-historic-garden-front-preview.png>)

| 文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| 原始GLB | 3,144,616 | 5b14a8923e5b02a667d356a648c6cc30ca1899a889ace0507fc893fa3c356085 |
| 网页近景GLB | 1,330,436 | ad11a4db0468738d16e8393be5ddca3d9ec9367f8e96e7c39791ccb33b28194d |
| 远景GLB | 741,224 | 35f3668815e9db67ac3f94d9a076c18a889155cc9fdac847207366bb05e78779 |
| Blender源文件 | 614,816 | 943b5e3f06050a7b991d5765346553a5aae1652fd877e80c87da74530fb87169 |

三档模型各通过 83 项独立射线检查，覆盖左右前翼每层三窗、较宽中央窗的窗框、两组壁柱、两片坡瓦、两枚顶饰、四根廊柱及柱旁净空、居中阶面、曲面顶棚、两端不同形制的附房，以及展件的边界。[探针和落点](surface-checks.json) [四种下载](../../../assets/models/candidates/xuhui-huaihai-1431-historic-garden-front/manifest.json)

登记采用公开地址的近似街区点。浏览器的档案展件由独立页加载，城市裁片、碰撞及现场模型数量均为零。1431号与1469号有各自的登记编号、花园立面和独立模型文件。[档案地点合同](final-placement-contract.json) [运行时登记预检](marker-preflight.json) [查看模型](../../../huaihai-1431-history.html)

从第一版原生渲染与410号近照的对照中补齐了弧廊下方的石台基，调整了瓦顶明暗和翼墙柱头。用原始、修订两版的同一对射线复核台基。[两版网格与射线实测](native-review.json)

桌面及390像素触屏各实测正面、斜视与俯视，校验两档几何的逐材料面数及四个下载文件。[移动与桌面实测](viewer.json) [桌面正面](viewer-desktop-full-front.png) [手机斜看四柱弧廊](viewer-mobile-full-oblique.png)

最终登记在已签目录中符合独立历史模型的运行约定。[正式地图登记复核](marker-final.json)

通过正式前后两站 HTTP 实取目录、运行模块、单体页、契约及四种发布件。新站登记211处，独立史料保留0个街区网格、0块裁片和0个碰撞体。[实际传输](signed-23k-http.json) [已签运行复核](marker-signed-23174.json)

正式31173与31174的普通目录分别为210处与211处。鼠标和390像素触屏从目录进入后，当代街区仍可见原有楼体。在同一街区点，前态及新增标记后的两端各三次取样都可通行，历史展件在主地图加载的三角面为零。[同机位前态](final-map-31174/before-same-overview.png) · [桌面地点](final-map-31174/desktop-location.png) · [触屏地点](final-map-31174/mobile-location.png)

两端都从地点卡打开档案、切换近远档，再返回同一标记。画面可辨中央四柱弧廊、花园阶面、双翼瓦顶和右侧低附房。该版本弹窗显示“1921—1939年照片”，展件说明保留了确切拍摄年份待考。浏览器签验了两档实际模型；独立页的六张视图及四个下载与这期文件逐件相符。[桌面近景](final-map-31174/desktop-archive-near.png) · [触屏远景](final-map-31174/mobile-archive-lod.png) · [两端操作及签名](final-map-31174/after.json) · [独立页对照](final-map-31174/bound-inputs.json)

首次前态因内存压力在首图前退出，桌面后态首轮则因检查器预期的标题与当期页面不同而中止。三次正式复测均退出成功，前态与后态共留下七幅画面。[首轮前态](final-map-31174/initial-control-failure/session.json) · [标题检查订正](final-map-31174/initial-caption-expectation/checker-correction.json) · [正式结果](final-map-31174/results.json)
