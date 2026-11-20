# 大上海大戏院历史立面

本模型表现1933年建成的大上海大戏院在1934至1937年照片中的西藏路入口。独立模型只包含临街立面，供按年代查看。今天的商场和影院沿用旧名称，市地方志已将1933年原院列入湮没建筑表。[地方志](https://web.archive.org/web/20160326003544/http://www.shtong.gov.cn/newsite/node2/node71994/node81772/node81779/node81794/userobject1ai108902.html) · [影院运营方的2013年地址](https://web.archive.org/web/20130907032513/http://love-zest.com/about.aspx)

上海市房屋管理局第一批名单的1A023号，将原名大上海大戏院、现名大上海电影院列在西藏中路520号。地方志与影院经营方记500号，历史摄影档案记500 Thibet Road，建筑档案记500 Yuyaching Road。这些地址写法均保留。华盖建筑师事务所、陈植设计的这座影院当年使用 Metropol 名称。南京西路216号的大光明大戏院和后来的上海音乐厅分别对应另两座建筑。[第一批优秀历史建筑名单](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [建筑档案671](https://www.virtualshanghai.net/Data/Buildings?ID=671) · [完整来源记录](reference-review.json)

## 几何依据

1934年日景记录两翼各四排横窗、入口两侧海报橱窗和向街面挑出的雨篷，夜景可以逐根数出八条发亮的竖柱。1937年Malcolm Rosholt的近正面照片可以看到这些柱子之间的七组竖纹长板、较短的横窗和下层玻璃，以及雨篷下面的较深门厅入口。另一张斜照记录了中英文竖挑牌。模型保留空白海报边框。[日景](https://www.virtualshanghai.net/Photos/Images?ID=35432) · [夜景](https://www.virtualshanghai.net/Photos/Images?ID=35431) · [1937年照片](https://hpcbristol.net/visual/ro-n1142) · [挑牌](https://www.virtualshanghai.net/Photos/Images?ID=1346)

宽23.70米和柱顶约21.83米是根据照片及五层尺度推定的建模值。黑白照片可以确认亮度和构造层次，颜色、金属反射和表面做法经过近似处理。屋顶、观众厅、内装和后部均缺少本次可核验的测绘依据。背面为展示截面，基础面设在临街立面中心。

## 重建

在项目根目录运行下列命令。构建依赖 Python、NumPy、Shapely 2.1、FontTools、Blender、Node.js、gltfpack、ImageMagick 及 oidnDenoise。渲染与网格、Blender 文件交叉检查复用项目的建筑打包工具。

```sh
python projects/shanghai/source/precise/huangpu-metropol-cinema-historic-front/source/build_metropol.py \
  --out /tmp/metropol/models --audit /tmp/metropol/audit --decoded /tmp/metropol/decoded
```

GLB 中 +X 为面向影院的观者右手，+Y 朝上，+Z 朝历史街道。Blender 文件内独立网格按立面、灯柱、雨篷和挑牌等部件分组。挑牌使用 Noto Sans CJK TC 重新命名的字形子集，具体字样、位置与厚度经过近似处理。字体保留 SIL Open Font License。[字体许可](source/fonts/OFL.txt)
