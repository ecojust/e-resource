# 上方花园24号张元济故居弄门

市房管局名录2D004登记淮海中路1285弄。2020年12月10日发表的到访照片和另一组摄影日期不详的铭牌近照共同辨认出24号临北支弄的低墙门洞、文保铭牌、电表柜及架空的波形雨棚。住宅分户点在1934号建筑内，独立故居标点在其北外缘，23号在4670号建筑内。门洞中心及细部尺度依照照片和地图估算。[来源和照片](../../../source/precise/xuhui-shangfang-garden-no24-entrance/reference-review.json) [原楼及邻户](../../../source/precise/xuhui-shangfang-garden-no24-entrance/footprint-review.json)

原始与网页近景各5,744面，远景3,504面。原始网格、实际解码的网页近景和远景各通过60个探针。11处地面样点辨认四个墙身点、门洞、棚下与公弄。门洞净宽约0.77米。五字“张元济故居”、两块铭牌、九个电表读数窗及雨棚都由独立几何表达。原生Blender另行重开，逐组比对原始网格。[三档探针](surface-checks.json) [原生重开与打包比对](geometry-native.json) [三档及可编辑文件](../../../assets/models/candidates/xuhui-shangfang-garden-no24-entrance/manifest.json)

建筑整体保留原1934号主体的140.27平方米及屋顶。同组近景67,274个原生三角面中，候选高度及平面范围内有532面。其与整个门楼边界的最小平面间隙为0.66米，远景为0.71米。主图碰撞按两块净墙截面确定，门洞和后方雨棚下留空。主楼、旁户与公共弄道均未裁剪。[主图合同](final-placement-contract.json) [源网格及地面测量](placement-geometry.json)

独立查看页在1250×820桌面和390×844触屏各完成三次切换，逐项验证原始GLB、压缩近景、压缩远景、Blender四个实际下载。实拍中能看到北侧两块铭牌、电表柜、棚下通风缝和贯穿的门洞。[独立查看页](../../../shangfang-garden-no24.html) [实测记录](viewer.json) [桌面正面](viewer-desktop-full-front.png) [手机斜视](viewer-mobile-full-oblique.png) [俯视雨棚](viewer-desktop-lod-above.png)

## 正式城景登记与文件复核

24号故居弄门由第198站登记为第199个城景入口。最终22162站共1,089个文件、997,749,445字节逐一经过真实HTTP与SHA-256核对。对照使用真实22161及22162目录和运行模块，后态近远两档各核实11个地面样点。主楼未裁剪，新增墙体独立参与碰撞，门洞保留空域。城景实拍另行记录。[HTTP收据](final-22162-http.json) [逐文件路径、字节与哈希](final-22162-files.json) [22161原始运行目录](final-22161-before.json) [22162登记后运行结果](final-22162-after.json)

七层服务在前后两代共取得133次实际HTTP响应，每个文件均匹配该层签名。154和160号单体页面订正后的字节也已逐层核验。前198个地点保持逐项一致，161的双近景绘制组校验工具仍在使用。[七层真实HTTP对照](seven-layer-http.json)

## 普通目录的路侧机位

从普通目录用桌面鼠标点击或手机触摸进入24号，原62°俯仰视角都能看见棚顶、左侧两块牌和右侧九格电表。原机位的眼点在保留住宅3713的外墙内约1.4至1.9米，低于17.94米屋顶。真实城市网格只绘制三角形正面，因此从屋内仍能看见弄门，深色背景横过门洞。初次把三角形双面都当作实墙，算出了整座弄门被挡。按实际单面材质重算后，两档城市网格都给出可见结果，与实拍吻合。[原桌面图](overview-correction/original-28162-desktop.png) [原手机图](overview-correction/original-28162-phone.png) [眼点、材质与逐像素对照](overview-correction/retained-3713.json)

正式31162采用朝向155.23°、俯仰44°。眼点在巷内，距离3713号住宅外墙约1.76至2.35米。实拍中门楣与两侧门边同时入镜，浅色巷道地面贯穿门洞，电表箱和铭牌的相对位置可以辨认。门旁上方浅牌原照写有“上海市文物保护单位”“张元济故居”，下方深色圆牌外缘可读“建筑可阅读”。普通目录图的牌文字号很小，五字主铭由原照和独立模型近景核对。[新桌面图](overview-correction/trial-30162-desktop.png) [新手机图](overview-correction/trial-30162-phone.png) [两端普通目录输入及图像签名](overview-correction/ordinary-directory-photos.json) [原照与字样](overview-correction/inscriptions.json)

照片取自30162试站的正常入口。31162正式站实际返回的入口、应用、相机模块和相机测试文件与试站逐字节一致。该机位绑定本栋网页模型的SHA-256。源码回归覆盖四款屏宽、其余158个登记候选以及本栋错误模型哈希。[正式站与试站的文件核对](overview-correction/final-31162-binding.json) [候选相机回归](overview-correction/candidate-http-and-regression.json)

## 主图上的门洞、铭牌与原住宅

原站同一弄内位置只显示住宅墙面和两扇窗。加入弄门后，在390像素触屏点正式目录，能同时看见灰瓦雨棚、贯穿的门洞和右侧电表柜。桌面收起导航后保留相同的44°俯角。从另一处地点实际点击地图灯牌，也回到24号弄门。正面近景能分清左侧上方的矩形铭牌、下方圆牌与右侧九个表窗；碑文细笔画在主图里偏暗。斜侧图可见棚下空隙和墙体厚度。选中标签覆盖棚顶中部，近景下的位置卡遮到部分墙脚。[原站同机位](city-31162/before-lane-detail.png) · [手机目录实点](city-31162/after-mobile-default.png) · [桌面](city-31162/after-desktop-default.png) · [灯牌实点返回](city-31162/after-desktop-beacon-return.png) · [正面](city-31162/after-lane-detail.png) · [斜侧](city-31162/after-oblique-detail.png)

主图两代各查11个地面位置。加入的墙面挡住四个取样点，其余七点保留门洞、棚下和弄道空域。原住宅1934与同组12座邻屋均保留，各自的地面与原始要素状态可在前后记录逐项对照。远景实际加载简化文件，四份交付物与独立页下载的哈希一致。最终正式站完整读回1,094份文件，共997,800,325字节。桌面与手机实测均无页面或HTTP错误。[前态](city-31162/city-before.json) · [后态](city-31162/city-after.json) · [远景](city-31162/after-distant.png) · [全站下载](city-31162/all-http.json) · [正式验收汇总](city-31162/release-evidence.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/80616706362db0c19423a80a57b4fce5a2c3084f/projects/shanghai/index.html#landmark=xuhui-shangfang-garden-no24-entrance&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，11 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
