# 中国纺织建设公司第五仓库临河弧券窗与中央门洞

南苏州路1295号仓库始建于1902年，列入上海市第四批优秀历史建筑。模型取2019至2020年临河一面的状态。两个外侧开间各有并排双窗，中央开间为三窗，上下两层共十四樘。上层深色钢框、下层木色窗扇、浅弧券、细铁花箱及各自的窗洞均独立成形。中央方门有层叠门套、方玻璃砖、立体字与两侧门牌。[市房管局建筑名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [《劳动报》现场报道](https://www.51ldb.com/shsldb/jiaoy/content/0175cae8a85fc001286748d88f2797bb.html)

临河墙宽27.50米，山花最高约16.21米。两侧轴间距4.127米的中央三券用于照片定标，另用宽柱、檐端及绿色1295门牌交叉核对。四站街景与报道照片分别得出27.34米、27.63米的外缘宽度。端部误差约1.25米，高度误差约0.8米。门扇后退1.49米，首1.25米为可进入的门腔。玻璃、窗框断面、店面陈设与紧接山墙的4.8米屋面为照片估计。仓库深处、整条侧墙、后院及室内办公层仍待调查。[四站交会](measurements/four-station-facade.json) · [尺寸复核](measurements/width-and-height.json)

报道原片相机朝真北188.807739°，相机记录的定位误差为9.43米。视线先与原城底图1070的北侧相交，2019年街景可从同一墙面读到1295门牌。西邻1305–1307号仍保留原两层楼和山字门头。两个数据源各移去本栋约91.07平方米的临街部分，原城余下约697.79平方米。部分主图鸟瞰角度可见较高的保留后楼。照片街位能看到山花轮廓。[门牌交会](measurements/green-address-and-portal.json) · [地块记录](footprint-review.json)

## 重建

从本目录运行以下命令。项目共用的封装脚本使用 Blender、gltfpack、Node、NumPy、Shapely、Pillow 和 fontTools。青砖小样、字体、测量参数及网格生成脚本均在本目录内。

```sh
python -B source/build_model.py --out builds/models --audit builds/audit --decoded builds/decoded
```

2015年青砖小样取自 Livelikerw 的署名照片，作了局部透视校正、重复拼接及表面明暗混合，按 CC BY-SA 4.0 分发。门牌和招牌所用字体子集遵循 SIL OFL。2020年报道照片、改造前航拍和街景仅用于测量对照。建筑几何及其代码按本仓库许可提供。[砖材署名与原始许可](source/brick-credit.md) · [字体源记录](source/entry_letters/origin.json) · [全部建筑来源](reference-review.json)
