# 毕卡迪公寓南向阶梯塔楼与534号入口

上海市住建委2023年修缮记录中的正面照片同时显示南向的阶梯冠部、两列深阳台和黑色方砖门厅。入口特写可辨三樘木门和门灯，二楼中央一对窄窗之间有黑砖窗间墙。悬挑雨篷的底面由三列凹格组成。较窄的上部横栏从雨篷前缘后退，三个开口中间宽、两侧窄。此次仅收录主楼南向花园的这段外观。[依据与分期](../../../source/precise/xuhui-picardie-apartments-south-front/README.md) · [上海市住建委修缮图](https://m.thepaper.cn/newsDetail_forward_23041937)

Blender工程保留106组可编辑网格，按构件、材质与朝向分组。近景有34,036个三角面，远景22,648个。近景与无压缩GLB的有向三角面逐一匹配，编辑工程经Blender重开并与原始网格比对。原生图由重开的工程渲染。[与修后照片对照](native-visual-review.json) [原生校验](geometry-native.json) · [原生预览](xuhui-picardie-apartments-south-front-preview.png) · [可旋转模型与四种下载](../../../picardie-apartments.html)

与修后正照复核后，模型补入黑砖门厅左右的低窗排，按2022、2024两期影像标定雨篷约15.55米宽，并依入口近照调整横栏及雨篷底面。阳台板前沿越过墙体竖边，栏杆位于板鼻后方。雨篷较深的底面与前缘浅色饰带独立建成，在同一条水平射线上前后相隔10厘米。三种独立序列化模型共通过435条射线，核对两列凹入阳台的门窗、挑板、栏杆、中央窄窗、阶梯屋面、三樘门、雨篷下净空及后部留空。[射线检查](surface-checks.json) · [检查程序](check-surfaces.py) · [入口近看](entrance-and-canopy.jpg) · [三排凹格底面](recessed-coffers.jpg)

南向原始轮廓边约39.81米。两期影像中雨篷位于边线中点偏西约2.67米和5.11米，模型采用偏西4米。主楼和后部在冻结城市底图中合为1958号地块，故截取南侧约31米宽的立面。原生近景裁入144.82平方米、保留4828.91平方米，远景裁入142.64平方米、保留4810.85平方米。独立建筑1834、774、1920和1504的近、远网格均未受裁面影响。35个地面探针核对了雨篷下可行空间、闭合的门扇、门墩、花园、保留主体和邻楼。[原始近远景与地面检查](placement-geometry.json) · [放置合同](final-placement-contract.json) · [屋面边线依据](../../../source/precise/xuhui-picardie-apartments-south-front/roof-registration.json)

地图默认方位2°、俯仰70°。桌面与390像素宽手机的相机预检同时容纳中央门、两列阳台及阶梯冠部。地面和取景结论来自绑定原始字节的网格与相机计算。[两端相机检查](camera-preflight.json)

原始版本承接244处场景，新增地标后为245处。之前1444个冻结输入逐个重读，共检查1,252,138,898字节。[父版本读取收据](parent244-readback.json) · [原始245处完整输入](production-snapshot.json)

十套场景版本从244处升至245处，逐层完成250次HTTP比对。最终验收站25208的1,467个文件共1,255,954,276字节，每份响应的SHA-256均与签名一致。用该站的运行文件复查后，全城裁面从1,503个三角形增加到1,509个，本楼增加6个。39处地面检查覆盖入口通行、主体和独立邻楼。全城地图中从目录点选这栋楼的实景验收仍待排期。[各版本输入对照](release-layers.json) · [最终站完整下载](release-25208-http.json) · [运行时放置与邻楼检查](runtime-placement.json)

独立模型页在1250×820桌面和390×844手机上分别切换近、远两档。四张实图均可辨中央阶梯冠部、左右阳台和底层浅色雨篷。页面四种模型下载与清单相符，浏览器未报告页面错误。[浏览器与下载记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png)

## 比卡迪公寓在31208的实际城景

前一版目录有244处。加入比卡迪公寓后，分别从390像素宽的手机和790像素宽的桌面目录选中衡山路534号入口。两端普通视距可辨中央竖窗和两旁窗列。窄屏顶端另有附近地标的标签，资料卡覆盖部分地层。前后两版另用同一440×380视窗、同一坐标和俯仰角拍摄，核对原楼块与修订后立面的变化。[手机首屏](city-31208/phone/map-mobile.png) · [桌面首屏](city-31208/desktop/map-desktop.png) · [同机位数据](city-31208/paired-street-view.json)

门前专幅能分辨正中的双扇、两侧窄门、横档和成对的壁灯。左、右门的下部各有一处受页面控件遮挡。上部近景见中央两列小阳台和两翼退台，补拍的宽屏斜俯视将完整阶梯屋冠移到目录提示下方，屋面高差和浅色边墙清楚可见。[门扇与壁灯](city-31208/architecture/map-three-doors-and-lamps.png) · [阳台和退台](city-31208/terraces/map-stepped-crown-and-balconies.png) · [宽屏屋顶](city-31208/roof-wide/map-roof-wide.png)

同一真实站点完成了39个地面位置检查与远档载入。鼠标、触屏分别从另一座已登记地标进入地图，实点本楼灯牌。远景检查从目录回到单体页保存四件文件。在另开的手机和桌面单体页，分别实看近、远两档，并再次保存原始、网页、远景和Blender四件，逐一核对字节数与SHA-256。14场实测均记录了浏览器退出。前态初次没有捕获浏览器PID、两次屋顶中断和第一次远景换页中断的原件均可复查。[鼠标实点](city-31208/physical-mouse/main-browser.json) · [触屏实点](city-31208/physical-touch/main-browser.json) · [独立页面](city-31208/standalone/viewer.json) · [退出记录](city-31208/map-process-outcomes.json) · [早期尝试](city-31208/previous-attempts/archive-index.json)
