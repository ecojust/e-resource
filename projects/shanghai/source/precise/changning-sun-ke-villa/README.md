# 孙科别墅主楼

上海市房屋管理局第一批优秀历史建筑名录以保护编号 **1M003** 登记「孙科住宅」，现使用单位列为上海生物制品研究所办公楼，地址为延安西路 1262 号。仓库工作名录对应第 047 行。长宁区政府及修缮报道使用番禺路 60 号上生·新所园区地址。这里建模的是园内孙科别墅主宅。名录二手转录中的年代为 1948 年，长宁区政府与保护修缮报道记载为邬达克设计、1931 年建成。2020 年修缮后向公众开放。[房管局官方名录](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [资料逐项核对](reference-review.json) · [长宁区政府资料](https://www.shcn.gov.cn/col6991/20231215/1250456.html) · [修缮过程与航拍](https://m.thepaper.cn/baijiahao_14106378)

模型表达南园三尖拱敞廊、上层四个圆拱开间与小铁阳台、东南圆弧开间、中央阁楼与北侧可穿过的车廊。旧照、研究所旧合影以及修缮后的不同方位照片共同约束南面。航拍用于判读屋顶、圆弧开间和院内附楼的关系。西侧隐蔽面、东西山墙、窗格、瓦、烟囱和尺寸均含估计。配楼、门卫室、花园及室内另计。[发布时标为「孙科别墅旧照」的照片](https://m.thepaper.cn/baijiahao_9972025) · [南北两面外观](https://www.thepaper.cn/newsDetail_forward_25656922)

本地 X 朝东，Y 朝北，Z 向上。建模锚点取具名地图轮廓中心附近，正面朝南花园。20.75 米是原粗模引用的栅格高度；本模型按主楼的两层和阁楼影像估算。生成器从零创建实体墙洞、门窗、筒瓦、屋顶和地基，模型不含第三方照片纹理。[地图来源与朝向](footprint-review.json) · [生成代码](source/villa_geometry.py) · [网页与文件清单](../../../assets/models/candidates/changning-sun-ke-villa/manifest.json)

从上海项目目录运行以下命令。需要 Python、Blender、gltfpack、ImageMagick 和 OIDN。

```sh
python -B source/precise/changning-sun-ke-villa/source/build_model.py \
  --out /tmp/sun-ke-villa/assets --audit /tmp/sun-ke-villa/audit \
  --decoded /tmp/sun-ke-villa/decoded \
  --gltfpack gltfpack --blender blender --oidn oidnDenoise
```

原创造型及材质采用 MIT 许可。地图源面适用 © OpenStreetMap contributors 和 Overture Maps Foundation 的 ODbL 1.0。附带的源高度记录引用 CNBH 2020（Qian Shi 等，CC BY 4.0）。引用的外部照片仅作研究参照。原作者与原始页面、影像散列见资料记录。
