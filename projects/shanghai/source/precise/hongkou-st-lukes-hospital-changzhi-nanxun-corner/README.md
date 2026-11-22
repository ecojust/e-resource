# 同仁医院旧址转角住宅

长治路155、157、159号与南浔路193号的四层街角楼，列入上海市第五批优秀历史建筑。市房管局表内的原名是同仁医院，现用途为住宅，建造年代为1920年代，保护类别为三类。1866年是同仁医局创办年。1923年的街簿将 St. Luke’s Hospital 列在 Seward Road 的 Nanzing Road 与 Boone Road 两个交叉路名之间，1925和1928年的名录均记作12 Seward Road。旧门号记录的是院址，院内不同时期还有其他楼房。[市房管局名录](https://fgj.sh.gov.cn/yxlsjzcs/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [名录原文与页码](measurements/st-lukes-register-directories-and-street-views.json)

## 从两条街看建筑

长治路一翼的山花围着一扇圆窗。山花下部，一道腰线把半圆形扇窗和下方三个方洞隔开。沿街再往左，是三道独立的落地拱门，中、右两拱之间有旧址铭牌。南浔路一翼的灰墙绕过三个窄折面与长治路相接。屋顶小塔中央朝街面为素壁，两侧各有窄窗。两翼坡瓦与街角塔冠在八个视角的独立页上可见。[打开模型](../../../st-lukes-hospital-changzhi-nanxun-corner.html) · [三拱门与扇窗对照](../../../data/audit/st-lukes-hospital-changzhi-nanxun-corner-v1/street-entrances/changzhi-ground-openings.jpg)

二至四层共50个沿街开口。长治路直墙24个，南浔路直墙18个，中间三个折面各有3、2、3个。转角中央中层有一段实墙。模型区分了退进的窗膛、石窗台、玻璃、分格木框和南浔路部分窗内的浅色封板。远端三轴依据2021年具名照片和两个相距8.74米的街景摄影点。2023年区刊只收进南浔路靠近街角的两轴及第三轴的局部。[上窗测读](../../../data/audit/st-lukes-hospital-changzhi-nanxun-corner-v1/upper-windows/README.md) · [屋顶与山花](../../../data/audit/st-lukes-hospital-changzhi-nanxun-corner-v1/roof-crown/README.md)

## 底层的年代差别

2015年3月的街景可见长治路山花下三个方窗的窗台与窗膛。Fayhoo在2016年2月6日从斜前方拍到上部扇窗。2021年1月同街位复拍时，三个下窗已封。另有2021年12月刊出的门廊近照，留下后退的门扇、上亮窗和水磨石地坪，该文没有标注拍摄日。2023年区刊所见为浅色展框。[原像测点](measurements/changzhi-ground-photo-observations.json) · [三种照片机位](measurements/changzhi-street-entrance-cameras.json)

南浔路底层在2015年3月、2017年8月和2019年5月的照片中仍有店窗。2021年1月6日从两向拍到连续的封墙、五处浅矩形凹面和六个上端悬块。中间的宽凹面上有两个悬块。模型按有日期的2021年照片表现这一段。店窗封合发生在2019年5月至2021年1月之间，照片没有给出具体施工日。区刊画面外的远三轴在2023年以后的状态仍缺少可核照片。[两机位与五处浅面](measurements/nanxun-lower-storeys-and-dated-panels.json) · [2019年街景记录](https://mapsv0.bdimg.com/?qt=sdata&sid=09000300121905291245388689H) · [2021年反向街景记录](https://mapsv0.bdimg.com/?qt=sdata&sid=09000300122101061622471425O)

## 尺度与模型范围

八个街景站的29条视线和两张具名照片约束了街角的六个端点。长治路和南浔路两段直墙分别约22.72米和15.83米，其延长线夹角约110.16度。模型原点采用两条直墙的虚交点。实景与底图的端点仍有约米级位置差异，背街屋面按2019、2021、2025年航片可辨的折线闭合。街面出挑与窗框进深是影像估值，室内格局缺少测绘依据。[街角定位](measurements/corner-street-ray-intersections.json) · [用地与周边保留范围](measurements/model-footprint-and-retained-owner.json) · [三期屋面](measurements/three-edition-roof-traces.json)

## 编辑和重建

在本目录的 `source` 中执行以下命令可分别导出近、远网格。各面与洞口的局部坐标按米计。将布局的 `ground_frontage_state` 设为 `published-2021-open`，可单独编辑2021年刊图中露出的门廊地面、门扇和铁栅。整包及可编辑源沿用上海项目的 Python、Blender 与 gltfpack 工具。

```sh
mkdir -p output
python build_model.py --output output/st-lukes-full.glb
python build_model.py --output output/st-lukes-lod.glb --lod
```

[门廊编辑源](source/changzhi_entrances.py) · [完整审核记录](../../../data/audit/st-lukes-hospital-changzhi-nanxun-corner-v1/README.md) · [出处与许可](SOURCES-LICENSE.md)
