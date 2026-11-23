# 亨昌里南口过街楼

模型覆盖愚园路1376弄的南入口、通向内院的过街廊，以及入口东边第一段连续红瓦屋盖下的街屋。第五批上海市优秀历史建筑5M006的登记范围还包括弄内4至42号和沿街1362至1374双号。旧《布尔塞维克》编辑部所在的34号在里弄深处，位于本模型之外。[上海市优秀历史建筑名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html)

## 两个观察年代

| 版本 | 南入口 | 街屋与内廊 |
| --- | --- | --- |
| 2018年2月 | 暖黄色粉刷、石质上拱、矩形窗和青绿色短雨篷，旧弄额仍在 | 还原沿街照片中的铺面分界、深浅窗扇和遮棚。旧廊保留可穿行空间及照片可辨的素墙。 |
| 2022年改造后 | 灰砖与红砖水平线、赤陶花叶山花、右起读作「亨昌里」的弄额、开启的铁门和酒红色上窗遮篷 | 五处铺口依2021年街景，东街楼上可见弧窗与编织围屏。廊内加入拱套、红褐窗扇、21块地址牌、历史展板、灯轨与长椅。2025年区府照片可复核门外浮雕和廊内陈设。 |

2018年塔楼上窗的窗台约在7.6米。2021年街景和2025年区府照片显示，改造后的窗台约在9.05米，窗头约在11.22米。2025年同一张照片上，铭牌上缘和窗台之间还留有约0.17至0.19米的墙带。[改造后的窗框](measurements/refurbished-tower-window.json) · [窗台与铭牌的实测间隙](measurements/refurbished-window-and-tablet-clearance.json)

两期的门楼西侧都保留一道浅浮雕盲拱。2015年和2021年的斜街视角露出了拱顶和北侧拱脚，其南侧轮廓被街边立柱遮住，模型以可见半边估算。它和更靠弄内的窄窗相隔约三米。更新后的酒红色折篷有四道活动弓、一根靠墙固定弓和两侧铰销。2020、2021年的东西向斜照可以交叉核对篷面轮廓。[背街侧的盲拱](measurements/west-return-blind-arch.json) · [折篷尺寸与重投影误差](measurements/refurbished-folding-awning.json)

更新后的外门上沿约为5.09米，往里可见一道横向灰色垂面，与廊内较低的吊顶相接。入口近照和廊内反向照片分别给出梁腹的前后边线，以及灰板约3.04至3.13米的底缘。梁背的遮蔽部分按两侧墙和吊顶封合。[南侧门头的照片测点](measurements/entrance-soffit-photo-observations.json)

## 尺寸与坐标

建筑坐标以街面西侧门墩底为原点。X沿街向东，Y指向弄内，Z向上。四期正射影像给出门楼正面宽约6.34米，街巷方向全长约16.2米。东侧第一段街屋沿街长约29.5米。2018年5312×2988原照经过两面透视校准，得到入口净宽约4.45米。新内廊的装饰墙净宽约3.98米、拱格约1.55米。这些尺寸属于摄影与航片估计，背面和远侧使用限定范围内的简化封合。[街面相机与误差](measurements/registered-street-camera.json) · [内廊量测](measurements/passage-2022-profile.json) · [街屋范围](measurements/entrance-and-first-east-roof.json)

## 制作入口

从本目录执行以下命令可以分别重建两期模型。三维图形、程序材质、文字许可和各构件的量测文件随源码提供。

```sh
mkdir -p output
python source/build_model.py --period 2022 --output output/hengchang-current.glb
python source/build_model.py --period 2022 --lod --output output/hengchang-lod.glb
python source/build_model.py --period 2018 --output output/hengchang-2018.glb
python measurements/calibrate_street_front.py --check
```

如需逐个检查网格的有向边和体积，可运行 `python measurements/export_checked_role.py full --out output/hengchang-audit`。另外两个角色为 `lod` 与 `historic`。[照片与许可](SOURCES-LICENSE.md)
