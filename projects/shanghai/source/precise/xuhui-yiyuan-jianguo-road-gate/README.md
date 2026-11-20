# 懿园建国西路南门

市房管局第二批登记2D018记为“懿园”，地址为建国西路506弄。南门的两扇铁门合拢时，中央形成弧顶，门后仍可透见总弄。门洞西侧另有一处小拱，东柱竖题弄名、外挂绿色门牌，随后一段围墙开五个方孔，上盖红瓦。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [各来源原件与校验](reference-review.json)

2013、2015、2019年的街景能看见打开的主门，两扇门的合拢状态取自2020年2月22日。按三个道路位置、四期全景中的可辨拱起点拟合，中央门洞估宽3.30米。单用2019年的两站估得4.14米。屋脊按4.46米建模，各视点独立估值约3.62至4.94米。题名位置、门牌内容与粗面外墙另据近照对照。字形、铁饰曲线、瓦件间距、门洞进深及墙背做了近似。[街景、视线与尺寸](street-registration.json) · [航片与底图](aerial-register.json)

底图中最近的两幢房屋各自保留。模型只覆盖弄口，西侧小拱内受遮挡的门扇、临时告示和其余院墙另列。修缮单位有18号和20号的照片，18号的商户地址点与具名地块边界仍有约12米出入，留待分户平面核定。[底图原件与邻楼](footprint-review.json) · [18号定位核对](house-18-location.json)

原创几何与材质按MIT许可。门牌及弄名字形采用更名的Noto Serif CJK子集，字库采用SIL OFL 1.1，第三方影像仅作研究。[字库来源与校验](source/fonts/provenance.json) · [字体许可](source/fonts/OFL.txt)

从上海项目目录可重建三档GLB、可编辑Blender文件、原生预览及模型校验记录。

```bash
python -B source/precise/xuhui-yiyuan-jianguo-road-gate/source/build_model.py \
  --out assets/models/candidates/xuhui-yiyuan-jianguo-road-gate \
  --audit data/audit/yiyuan-jianguo-road-gate-v1
```
