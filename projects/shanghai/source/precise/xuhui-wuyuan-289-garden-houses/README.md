# 五原路289弄花园住宅

从五原路的铁门进入内弄，西侧依次为北栋1–2号和南栋3–4号。两座建筑各有一组大小不同的都铎式山墙。沿弄可见红砖下层、浅色粉墙中的深色木构、凸出的窗间和弧形砖砌梯墙。楼下券门分别通往1号和3号。从弄堂转上室外楼梯，分别可到2号与4号。[独立浏览页](../../../wuyuan-289-garden-houses.html) · [现场门牌与分栋](measurements/identity-and-chronology.json) · [栋位与屋顶平面](measurements/site-plan.svg)

1935年建筑师相册收有东立面与施工时全景，能辨出面向花园的尖券门廊、楼上木敞廊、陡坡瓦面和砖烟囱。北栋的两道相邻窗、外开的窗扇、转角台阶与逐级升高的梯墙按另一张能读到1号和2号的照片调整。南栋两处取景可交叉复核小出窗的进深、铁门、三阶入户踏步和门牌。模型中的北栋西北角按城市底图和航片收进，两栋中心相距约21.33米。[建筑师相册](https://brs.russianshanghai.city/architects/a-l/v-n-dronnikoff) · [北栋窗与拱门登记](measurements/north-numbered-camera.json) · [南栋木构与门牌](measurements/house-three-street-front.md) · [四期航片和原地块](measurements/paired-house-placement.json)

2017年从五原路拍下的弄口照片记录了两扇铸铁门、左扇内的小门和14块上下分列的卷花。照片中门宽约为门高的1.30倍。模型单独制作了门扇、回纹边、花纹、拉手和两片之间的门缝。绝对高度采用2.16米的摄影估值。两处缝线在照片与模型间约差4厘米，左下角在照片中被树遮住。[2017年弄口照片](https://commons.wikimedia.org/wiki/File:五原路289弄住宅.jpg) · [照片与模型对照](../../../data/audit/wuyuan-289-garden-houses-v1/registration/2017-north-gate-and-model.jpg)

现场历史建筑铭牌记公和洋行设计、1933年竣工。建筑师相册题记为1935年，房管介绍另记1930年。住宅地址和四个门号有独立证据。隐蔽背墙、屋脊高程、院内划界和套内房间缺少完整原图。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [房管建筑介绍](https://m.thepaper.cn/baijiahao_16359621) · [出处与许可](SOURCES-LICENSE.md)

## 重建

从此目录运行以下命令。网格生成依赖 NumPy、Shapely 和 Pillow，摄影配准使用 SciPy。网页压缩和编辑工程分别需要 gltfpack、Node 和 Blender。

```sh
python source/finishes.py
python measurements/check_mesh.py build/source
python source/package_model.py build/source build/packaged
python source/package_editable.py prepare build/packaged build/native
python source/package_editable.py run build/packaged build/native
```

浏览页从资产目录中的 manifest.json 读取原始 GLB、网页近景、远景以及 Blender 可编辑工程。作者摄影机定义在 source/cameras.json。最终交付的四件、检查结果和浏览实图可由同一份记录追溯。[模型复核](../../../data/audit/wuyuan-289-garden-houses-v1/model-review.json)
