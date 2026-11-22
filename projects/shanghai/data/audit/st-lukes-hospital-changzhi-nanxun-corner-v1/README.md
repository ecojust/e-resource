# 同仁医院旧址转角住宅 · 模型核验

本页记录长治路与南浔路转角四层旧楼的整楼核验。五个街面都按可见墙面开洞，楼上总计50处开口。模型采用米为单位。2015至2023年的地面照片支持沿街细部，三期航片约束屋面平面。塔背与后侧山墙的可见资料较少。[独立模型页](../../../st-lukes-hospital-changzhi-nanxun-corner.html) · [建筑与年代](../../../source/precise/hongkou-st-lukes-hospital-changzhi-nanxun-corner/README.md) · [摄影、名录与许可](../../../source/precise/hongkou-st-lukes-hospital-changzhi-nanxun-corner/SOURCES-LICENSE.md)

## 影像和几何

| 对象 | 检查方法与读数 |
| --- | --- |
| 五个街面、两翼瓦顶 | 八个街站的29条视线拟合街墙，联合两张具名照片定角。主体影像检查的35个固定像点有34个先击中指定材料。街墙、饰带及瓦面用完整三维模型互验。[街面检查程序](../../../source/precise/hongkou-st-lukes-hospital-changzhi-nanxun-corner/measurements/check_street_surfaces.py) |
| 二至四层窗 | 各档均实测359条截面射线。同一窗内分别检查框、梃、玻璃、石台或封板，359条均先击中指定部件。另存131条照片射线，逐处记录街树、檐边和灰色洞膛的影响。[上窗证据和模型图](upper-windows/README.md) |
| 长治路底层 | 2023年区刊26点有24点在三像素邻域内中对应材料，2021年街景23点中21点，Fayhoo的2016年山花局部19点全部直接命中。四个偏差集中于窄饰边与抹灰墙的交界。三档对整栋求第一处交面。[68个原像点与实测](street-entrances/three-mesh-photo-checks.json) · [三机位模型图](street-entrances/changzhi-ground-openings.jpg) |
| 南浔路底层 | 五处浅凹和六块悬饰按2021年两向街照定位。各档57次截面检查全部先击中指定构件。[近档截面](nanxun-ground-panels/panels-full.json) · [远档截面](nanxun-ground-panels/panels-lod.json) |
| 圆眼山花和街角小塔 | 三档各有84条几何射线全部通过。两张照片的固定像点分别命中38/40、23/28。圆窗凹口、塔窗边和塔背定位另有逐项说明。[塔冠测读](roof-crown/README.md) |

2015年、2017年和2019年可见的南浔路底层店窗，到2021年1月两向街照中已封合。浅矩形面与上端悬块按这次拍摄的实像逐处定位，远端外墙的2023年状态受区刊画幅所限。长治路的三拱、上半圆窗及腰线下的三个方洞分开测量。[南浔路两个方向的测量和年代](../../../source/precise/hongkou-st-lukes-hospital-changzhi-nanxun-corner/measurements/nanxun-lower-storeys-and-dated-panels.json) · [南浔路浅凹首交记录](nanxun-ground-panels/panels-raw.json) · [长治路原照测点](../../../source/precise/hongkou-st-lukes-hospital-changzhi-nanxun-corner/measurements/changzhi-ground-photo-observations.json)

## 查看与复算

独立页提供八种机位。每个按钮分别在桌面1024 × 690与手机390 × 760的真实页面上操作，截图保存的是当时的三维画布。桌面和手机分别切换近、远及自动选档，并另行检验滚轮拉远和近镜复位。三种下载逐份从普通链接保存，按实际字节数与SHA256复核。[逐图观察及下载校验](ordinary-ui/browser-ui-review.json)

近档63,632个三角面，720个闭合部件按707个名称分组。远档48,634个三角面，649个闭合部件按636个名称分组。图像检查分别读取未压缩的原始网格、独立解码的近景与独立解码的远景。照片位置允许的邻域与构件截面的通过判据分别记录。照片权利人保有原图，模型专题板和网页截图只含项目自主绘制的几何与材质。[建筑代码与复算入口](../../../source/precise/hongkou-st-lukes-hospital-changzhi-nanxun-corner/README.md)
