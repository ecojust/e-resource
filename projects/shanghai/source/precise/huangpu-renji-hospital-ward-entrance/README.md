# 仁济医院西院2号住院楼庭院入口

市房管局第二批登记表将山东中路145号列为2A028麦家圈医院，公布时使用仁济医院名称。院方、上海交大及2024年黄浦区政务现场报道将此处原住院楼追溯至1932年。院方还分别记载住院楼2013年修缮、门诊及综合楼于2014年及2015年另行改建。[名称、年代和图像核对](reference-review.json)

2010年实照的蓝色2号楼牌位于灰砖院墙中央的浅色楼梯塔下。2020年和2024年两幅独立实景可在同处读到圆形2号，右侧楼翼另有3号。此次呈现2020至2024年记录的入口，包括两侧灰砖窗带、东侧栏廊四个窄窗、石塔三排楼梯窗、门廊大窗及下方拱顶。现有院区范围内另有门诊楼等多座建筑。[2020年正面](https://service.shanghai.gov.cn/sheninfo/featuredetail.aspx?Id=45c65707-2c0c-4a13-99b2-2f612967a3af) · [2024年黄浦现场](https://m.thepaper.cn/newsDetail_forward_28290833)

2号楼及2号楼南门的两个独立地址点均落在原生1977，4号楼及门诊楼两个点则落在740。原生1977与目前OpenStreetMap的房屋边界重合约98.05%。模型对准其较宽的南向内庭端墙，跨度约24.74米。高程和细部为按照片比例估算，未建造其他庭院楼翼、室内及完整屋面。[底图、影像和空间证据](footprint-review.json)

从上海项目目录复建，Blender、gltfpack、ImageMagick及oidnDenoise须在PATH中可用。

    python -B source/precise/huangpu-renji-hospital-ward-entrance/source/build_model.py --out /tmp/renji-model --audit /tmp/renji-audit

生成的三份GLB与可编辑Blender文件使用原创程序化网格及材质。参考影像由原出版方保有，文件内只存来源与SHA-256。
