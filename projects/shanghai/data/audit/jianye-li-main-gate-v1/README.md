# 建业里总弄沿街门楼

建国西路上的三个相似门楼中，中门有两组三扇木窗和五字额。2014年正面原照可见右起书写的「建業里總衖」。2020年三个道路相机上的同一门楼已经改成左起书写，额下增加CAPELLA铜牌。两边另外两处窄门为单组窗、三字额。本次按2020年照片制作门楼外侧可见体量。[历史门牌和更新经过](../../../source/precise/xuhui-jianye-li-main-lane-gate/README.md) · [街景、署名及照片](../../../source/precise/xuhui-jianye-li-main-lane-gate/reference-review.json) · [九个部位的图像高度对照](elevation-photo-comparison.json) · [独立模型](../../../jianye-li-main-gate.html)

近景有14,256个三角面，远景6,876面。重开Blender工程后实际检查41个可编辑网格和10种材质。三份网格分别通过102条射线，包括36块玻璃、窗扇、五字额、小铜牌、石柱、檐间回纹、女儿墙、门洞和后侧截取位置。独立模型页和四个下载文件均已通过HTTP字节检查。[原生工程及解码](geometry-native.json) · [原生渲染](xuhui-jianye-li-main-lane-gate-preview.png) · [观察记录](visual-review.json) · [射线检查](surface-checks.json) · [独立页及下载签名](standalone-http.json)

地图使用119号沿街建筑的实际南墙，截取中间门楼的一小段。原近景保留99.17%、远景保留99.19%，门楼两侧与后侧由3段截面连接。两根石柱计入碰撞，公共人行道、门洞中线和所见退进可通过，退进后的既有建筑保持阻挡。默认相机朝344°、俯仰28°，以两种屏幕的正常应用相机分别检测七处门面特征，全部可见。街对面2263的原始高度会遮住更低的视线，已按现场关系保留其体量。[地块与三个街面相机](../../../source/precise/xuhui-jianye-li-main-lane-gate/footprint-review.json) · [两档城市几何](placement-geometry.json) · [放置与地面](final-placement-contract.json) · [实际相机计算](overview-sightlines.json) · [到地图查看](../../../index.html#landmark=xuhui-jianye-li-main-lane-gate&mode=overview)

修正后的独立页将正视按钮标为“建国西路正面”。桌面与390像素手机均已打开实际页面、切换近远景并取得四件文件。四视图可见五字凸额、两扇窗及敞开的门洞。[实际四视图与下载结果](viewer-fixed/viewer.json) · [两处标签的版本记录](viewer-caption-layer-http.json)

正式22149地图输入实取981个文件，均与签名相符。渲染器按宏区分页，城市988个裁切三角面分布于20个宏区，门楼所在近景源的两片均只绑定119。18个地面检查点及12项向量源检查通过。[地图传输](frozen-http-summary.json) · [裁切与通行核查](runtime-placement.json)

建业里独立页的街面按钮已校正为“建国西路立面”。原有七组城市服务逐一返回校正后的网页，保留同期模型、相机和建筑目录。[实际页面核对](viewer-caption-layer-http.json) · [两次街名修订的历史收据](../development-building-v1/viewer-caption-correction/summary.json)

正式24149地图将全市目录从185处增至186处，原有145条候选记录逐项一致。十张实图中，改造前同一街段的连续窗墙在中部形成门楼开口，改造后可见两侧石柱、分层女儿墙和成对木窗。窄屏默认视距可辨轮廓，放大后可分辨窗扇。地图视角较高，五字额的字形以独立页正视图最清楚。街面和俯视图均保留两侧原有楼体以及街对面近景遮挡。按地点搜索切换到吉祥里，再返回建业里后，门楼重新载入。[同一街段前态](city-24149/map-before.png) · [桌面默认视距](city-24149/map-desktop-same-camera.png) · [手机放大](city-24149/map-mobile-public-zoom.png) · [街面](city-24149/map-street-facade.png) · [回返](city-24149/map-returned.png)

手机触屏和桌面鼠标分别在真实画布上命中门楼标签。桌面第一次松键发生在监听建立之前，随后在同一窗口同一标签再点一次，收据保存了浏览器确认的鼠标事件。地图中18个地面点逐项符合门柱、门洞和街面的预期。正式站共实取986个文件，合962,072,528字节，全部符合签名。[双端操作及下载](city-24149/main-browser.json) · [桌面复点](city-24149/repeated-mouse.json) · [整站传输](city-24149/149-all-http.json) · [汇总](city-24149/result.json)
