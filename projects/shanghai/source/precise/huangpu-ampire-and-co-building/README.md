# 安培洋行大楼圆明园路主立面

上海市房管局第二批优秀历史建筑表中，2A023一行写「洋行／上海广告公司／圆明园路97号」。佳士得于2014年8月21日发布的新址公告称这幢建筑始建于1907年。OSM的年代属性记1911年。后期安培洋行的名称用于识别这幢楼。上海广告公司、安培洋行和佳士得是不同年代的使用者。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [佳士得新闻稿，第2页](https://press.christies.com/wp-content/uploads/2023/09/b69ba395cd03841ca0a35d5040aceb91.pdf)

Livelikerw在2014年1月27日从圆明园路拍摄的正面照片可辨四排楼层窗。首层中央为宽拱门，三层圆形挑窗落在石承托上。两侧各有三开间，两扇二层窗有弧形窗冠，顶层有一对三角山花。2020年6月17日发布的近距离斜照进一步显示，两端凸翼呈半圆形，每层沿弧面开三窗，窗下环绕一道水平腰线。模型以实照片段为准，砖缝、弧度、玻璃、层高与浅返进深均为估计。登记表的「三层」记法另存。建筑背面、室内及各时期使用情况仍待独立调查。[正面原片](https://commons.wikimedia.org/wiki/File:Ampire%26Co._Building_Shanghai.JPG) · [两端斜照与门洞近照](https://www.meipian.cn/3035vdac) · [资料记录](reference-review.json)

圆明园路97号的门牌兴趣点和商业场所点都落在具名建筑地块1125内。冻结地块与OSM w380339971第6版的交并比为98.60%。此模型仅替换约3.8米深的街面，普通城市近、远两档分别保留原地块投影的82.15%、82.35%。与115号圆明园公寓及其余同组建筑保持独立。两道截面沿实测边界封口。[落位记录](footprint-review.json) · [模型与地图实测](../../../data/audit/ampire-and-co-v1/placement-geometry.json)

## 生成模型

在项目的 projects/shanghai 目录运行以下命令。需要 Python、NumPy、Shapely、Blender、Node.js、gltfpack、ImageMagick 7 和 Open Image Denoise。

```sh
python source/precise/huangpu-ampire-and-co-building/source/build_model.py --out ./build/ampire-assets --audit ./build/ampire-audit --decoded ./build/ampire-decoded --gltfpack /path/to/gltfpack --oidn /path/to/oidnDenoise
```

原创几何和脚本遵循项目MIT许可。门牌归属参考OpenStreetMap贡献者数据（ODbL 1.0）。Livelikerw照片采用CC BY-SA 3.0，作为形状研究资料；模型使用程序生成的独立材质。[独立模型页](../../../ampire-and-co.html) · [下载清单](../../../assets/models/candidates/huangpu-ampire-and-co-building/manifest.json)
