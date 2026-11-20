# 长阳路147号历史门楼

2014年街对面照片和2015年1月的正面与侧面照片用来比对石额挑出、凹槽柱、砖框和下部石基。重开编辑档后的首版画面将红砖条带延续到了地面。根据2015年照片，修订版补上两段石基，并减小叠砖条出挑。最后的原生画面可辨退台、竖槽和右侧直牌。[初版](preflight/initial-street-face.png) · [修订版原生画面](hongkou-tilanqiao-historic-front-preview.png) · [外部照片及发表日期](../../../source/precise/hongkou-tilanqiao-historic-front/reference-review.json)

Blender 4.3.2重开后，40个网格保有15种原创建筑材质，三角面及逐材质坐标与未压缩GLB相符。独立解码网页近、远档后，连同原始档，各检查24处立面材料和8行真实字形，共96项。近景28,296个三角面，远景17,204个。[原生与模型比较](geometry-native.json) · [三档逐项观测](relief-checks.json) · [复核程序](check-relief.py)

旧址门楼与道路标线、浅色铺地、左侧白色楼和右侧树木的相对位置在四期航片中可辨。用保留的1447街面边界约束模型厚度，定位为约2至3米级估计。四个城市近瓦片和对应远景均逐个三角面比对。最近原始近景离门楼0.060米，远景0.138米，OpenFreeMap在线矢量面的最小间距82.75米。底图保留原状。2014年照片自带的坐标偏离长阳路；陈列馆的147号地址点也不能替代门楼中心。[四期街面影像、定位与弃用坐标](street-framing.json) · [街面位置依据](../../../source/precise/hongkou-tilanqiao-historic-front/footprint-review.json) · [原始资产与距离](placement-geometry.json) · [地图放置参数](final-placement-contract.json)

126处正式预演场景逐一读取396项输入共266,484,145字节，包含地标、目录、页面和模型下载。[全部HTTP记录](frozen-scene-http.json)

在126处入口的地图上，通过 HTTP 实取带版本号的三份地图登记表，以及按 SHA-256 寻址的普通建筑总表、分区索引和替换表。共核对14个请求，返回字节与冻结清单一致。[逐次请求](metadata-cache-http.json) · [本次调整涉及的文件](runtime-input-changes.json)

普通建筑缓存键更新后，最终126处测试站的397个冻结输入，加七个城市原始源文件，全部重新从HTTP实取核对。共404次成功响应、268,670,049字节。目录中此前125处记录逐项相同。[逐文件状态、字节与散列](ordinary-key-http.json)

125处的旧站能在该街面加载两个相邻原生体块，实际近景组含18栋、105,098面。126处新增街面构件后，两处邻楼仍使用各自原生几何。[前态整屏](control-125/street-before.png) · [运行记录](control-125/control-browser.json)

已载入邻楼的126处站内，从原目录进入后在同一会话比较−51°朝向下的61°和57°俯角。前一机位被邻楼68挡到门扇，下调至57°后两端都能看清门扇下缘和竖牌。浏览器实测眼位回放到原楼网络模型及四组邻屋原生网格；61°时，手机9个取样点中有5个首先命中邻楼，桌面有2个，57°时两端各9点均首先命中街面构件。[手机61°](camera-comparison/map-mobile-with-neighbors.png) · [手机57°](camera-comparison/map-mobile-57.png) · [桌面61°](camera-comparison/map-desktop.png) · [桌面57°](camera-comparison/map-desktop-57.png) · [实测眼位与射线](camera-comparison/visible-street.json)

同轮浏览覆盖街面、远景和四件实际文件，并核对场景中两栋邻屋的状态。首次脚本对MapLibre返回的60.99999999999999°与61°做过精确整数比较，已留存当时的冷暖视角和失败现场；上面的同会话复测将角度容差改为0.0000001°。[两档与下载收据](camera-comparison/main-browser.json) · [首次记录](camera-comparison/initial-check/main-browser.json)

正式采用57°俯角后，在126处入口的新目录（SHA-256以 `149b8d333dede671` 开头）从普通地点卡重新进入。390×844手机触摸和870×660桌面点击均直接落到−51°／57°，门扇与右侧竖牌在两端可见。街边仍保留邻楼及其前景遮挡。两端均加载28,296面近景，所在18栋原生组共105,098面，未裁任何原生面。每幅截图前连续核对4帧相机停稳、启动遮罩已消失。404项HTTP读取共268,670,049字节，与正式输入逐字节对应。[手机原图](registered-default-57/map-mobile.png) · [桌面原图](registered-default-57/map-desktop.png) · [两端实际选择与画面散列](registered-default-57/main-browser.json) · [正式输入收据](registered-default-57/frozen-http.json) · [复核程序](registered-default-57/check-final-defaults.cjs)
