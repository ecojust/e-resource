# 延庆路130号住宅南向庭院立面

市房管局第二批优秀历史建筑名录将延庆路130号登记为徐汇区2D048，原名称为“住宅”，公布时的使用单位是结核病防治中心。市文化旅游局的图文记载这座三层砖木住宅于1928年建成，同时刊出了标记地块的1948年行号图、早期照片、庭院正面、屋顶鸟瞰和窗楣特写。街对面延庆路135至149号属于另组花园里弄住宅。[市级原表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) [市文化旅游局图文，人民网上海频道2023年8月18日刊发](https://sh.people.com.cn/n2/2023/0818/c350122-40537216.html)

Livelikerw于2016年2月6日拍摄的照片补充了底层门窗、石阶、花盆栏板的前后关系。主厅向南院突出，弧形边沿承托着二层露台。左右两端的短柱托起弧形山花，下缘各有一排可透光的石栏。两端之间有后退的棚式老虎窗，后方为红色平瓦铺成的孟莎式屋面。模型只制作至这一侧屋坡，窗格及券心人物头像用照片可分辨的轮廓表示；层高、细部进深和瓦缝间距均为估计。[2016年庭院实照，CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:130_Yanqing_Rd._Shanghai.JPG) [图像时间、来源与校验值](reference-review.json)

两期正射和鸟瞰均可辨认南面的一对屋冠、背后较长的红瓦屋面、东侧单独长屋及西侧附房。诊疗单位名点落在南院内，实际主屋使用城市底图14-13719-6695的2164，其足迹与OSM轮廓w1202291109重合97.65%。北侧剩余体量、附房及沿街院门另作保留。地图位置为121.44579470, 31.21700160，对应主厅南边线中点。[底图与配准说明](footprint-review.json) [航片版本与原始图块签名](aerial-editions.json)

近景有30,092个三角面，远景有12,452个。Blender母模、原始GLB及近远两档均在独立页可下载。各档只包含原创网格和材质，参考照片著作权归原作者。[单体查看与下载](../../../yanqing-road-130.html) [在主地图查看](../../../index.html#landmark=xuhui-yanqing-road-130-residence&mode=overview) [落位和实物查验](../../../data/audit/yanqing-road-130-v1/README.md)

## 重新生成

在仓库根目录运行以下命令。所用工具包括Python、NumPy、Shapely、Blender、Node.js、gltfpack、ImageMagick和Open Image Denoise。

```sh
python -B projects/shanghai/source/precise/xuhui-yanqing-road-130-residence/source/build_model.py \
  --out ./build/yanqing-assets --audit ./build/yanqing-audit --decoded ./build/yanqing-decoded
```
