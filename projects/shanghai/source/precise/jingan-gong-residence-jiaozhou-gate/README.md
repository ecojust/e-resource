# 龚氏花园住宅胶州路522号拱门

上海市第四批优秀历史建筑名录4B017登记龚氏花园住宅，现名宝钢老干部活动中心。本模型重建胶州路522号临街独立院门。院内住宅与南侧胶州路510号分别有自己的足印和名录记录。[上海市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [原城配准](footprint-review.json)

2015年正面照可辨两座砖墩、灰色勒脚、带矩形凹板的柱帽、浅色拱圈、三根主铁辐与扇形卷草。右门扇接近关闭，中央开口和细铁竖条可见。2024年斜向近照补充了左侧内开的门扇、黄色慢行牌和拱底厚度。模型采用2015年的铭牌与圆形灯具。2024年照片里的绿色门牌和红色设备记录在来源表中。[2015年正面照](https://commons.wikimedia.org/wiki/File:522_Jiaozhou_Rd._Shanghai.JPG) · [2024年上海静安图文](https://www.thepaper.cn/newsDetail_forward_27269259) · [逐项观察](reference-review.json)

## 尺寸与街面

两组街景交会和正面照的平面校正给出约3.62米净洞宽。模型起拱高3.86米，内拱顶约5.69米，外压顶6.47米。正面照片的尺度、透视与读点误差使外高估计范围约为6.12至6.83米。砖的砌筑缝、铰链进深与门扇开启角均为估计。两片门分别向院内转约82度和7度。[街门测量](measurements/street-gate-survey.json)

原城街屋2100的北端挡住一部分门洞。近、远景分别局部切去该处挡墙，院内住宅1778和邻处3183保留。地面验收沿通行线确认约1.25米宽和7.05米长的连通空间。[定位记录](../../../data/audit/gong-residence-jiaozhou-gate-v1/placement-notes.md)

## 模型与重建

原始和近景各48,606个三角面，远景26,102个。两档分别保留有厚度的拱底、砖墩、透空铁花、铰链、门扇、铭牌和慢行牌。远景减少砖侧面、圆弧和卷草的细分。原始几何按189个具名编辑组组织，提供六个有目标点的正交编辑相机。局部坐标使用米，面向院内时X轴向右，Y轴向院内，Z轴向上。

在仓库根目录运行以下命令。需要项目使用的 Blender、gltfpack、Open Image Denoise 与 Python 几何依赖。

```sh
python projects/shanghai/source/precise/jingan-gong-residence-jiaozhou-gate/source/build_model.py \
  --out build/gong-gate-assets --audit build/gong-gate-audit --decoded build/gong-gate-decoded
```

## 署名与许可

建筑、砖墩、拱圈、卷草和门扇的原创几何使用项目MIT许可证。Livelikerw于2015年1月22日拍摄的《522 Jiaozhou Rd. Shanghai》采用CC BY-SA 4.0。三块铭牌从原照裁剪、校正、缩放并拼成贴图。慢行牌的黑色字形从同一照片分离、简化并挤出。铭牌图集、字形坐标及其对应材质和几何沿用CC BY-SA 4.0。2024年的图片仅用于辨认构件。[原作及作者](https://commons.wikimedia.org/wiki/File:522_Jiaozhou_Rd._Shanghai.JPG) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) · [贴图制作](source/plaque_samples.py) · [字形制作](source/caution_sign.py)
