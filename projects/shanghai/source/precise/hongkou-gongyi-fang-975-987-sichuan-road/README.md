# 公益坊3号楼 · 四川北路975–987号

这栋三层商住楼在海宁路口，面向四川北路。二、三层各有九跨通长阳台，底层沿街开店。虹口区记其建于1936年。北面另一栋列入同条保护名录的公益坊在四川北路1297–1311号，两栋最近端点相距约56米，中间是后来新建的2号楼。[虹口区楼号与门牌](measurements/sichuan-road-5f038-two-addresses.json) · [1号楼模型](../hongkou-gongyi-fang-1297-1311-sichuan-road/README.md)

| 部位 | 模型依据及精度 |
| --- | --- |
| 沿街楼身 | 十个街景机位分别定位南、北端，算得沿街长度46.59米，城市底图561号轮廓约46.31–46.48米。模型取46.50米，进深约12.82米，两层阳台板高约4.51米和8.61米。[街景交会](measurements/registered-frontage-street-rays.json) |
| 木门和底铺 | 2018全幅定九跨，修缮后街照可逐樘量读北四跨的十六组阳台门与四个铺面。第七跨二层有一扇向内开启，开启角度取近似值。南五跨采用相同楼层、相同位置的尺寸中位数，铺门开向留作估计。[逐樘读数](measurements/three-building-front-shop-and-door-dimensions.json) |
| 外廊 | 两层各九跨栏片、十道支承轴线；每跨有六辐圆心、四角卷花、竖条、横档和檐托。对照2018年照片与修缮后的斜视照片辨认透空、铁花和托座。[原像记录](measurements/balcony-photo-traces.json) |
| 海宁路端墙 | 三层四洞，二层三洞。2015年街景显示高低不同的窗帽，2020年2月两站看清二层西洞。2022年1月刊发的夜景能辨二层全部三个凹口及三层至少两处；照片无法分清内部填料。模型保留洞深和窗帽，用哑光暖暗色表示凹面。[修后夜景](measurements/south-short-wall-post-repair.json) |
| 屋面 | 2018年12月设计单位照片显示街侧纵坡、院侧三道横向瓦坡与两处凹口。修后改为沿街灰蓝窄坡、中央露台、两端深浅分区，2025年影像还能辨明北侧深色底上并列的两道浅色带。屋顶设施用途、高程及板材质为估计。[影像日期与屋面线](measurements/roof-2018-2025-documentary-geometry.json) |

街面装饰、阳台和屋面是本轮细化重点。院侧西墙保留简化围护，内部房间和自四川北路不可见的开口仍缺独立资料。城市定位仅指向本楼的底图561号。按实测街角放置后，底座投影596.13平方米，与561号相交557.37平方米，原图斑余62.08平方米。底座越出原图斑38.76平方米，反映了底图和街景的配准差。与中间627号、北侧3085号的地面重叠均为零。[定位依据](measurements/placement-identity.json) · [三份落地网格计算](measurements/registered-plinth-and-retained-city-source.json)

## 重建

从本目录运行以下命令。模型采用米，街角为原点，沿街向北为X，向院内为Y，竖直向上为Z。导出GLB时转换为glTF坐标。

```sh
python source/build_model.py --output gongyi-3.glb
python source/build_model.py --output gongyi-3-lod.glb --lod
python source/build_model.py --output gongyi-3-2018-roof.glb --roof-period 2018_roof_study
```

第三条命令重建2018年屋顶，街面保持同一对照底本。生成原始、网页和远景GLB以及可编辑Blender文件时使用以下入口，需安装项目所用的Blender、meshoptimizer、ImageMagick和Open Image Denoise。

```sh
python source/build_model.py --out dist --audit audit --decoded decoded
```

砖缝、瓦面都是程序原创。修后默认模型仅使用红砖纹理，旧屋面研究另用瓦面纹理。页面可从街面、南墙、屋顶及门窗栏杆等八个机位查看。[独立预览](../../../gongyi-fang-975-987-sichuan-road.html) · [来源与许可](SOURCES-LICENSE.md) · [核验记录](../../../data/audit/gongyi-fang-975-987-sichuan-road-v1/README.md)
