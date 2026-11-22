# 龙柏饭店2号楼的双扇老虎窗与草坪柱廊

虹桥路2419号的2号楼曾是《上海泰晤士报》报社。长宁区规划资源局将其记为1930年代的英国乡村别墅，位置在饭店进门东侧，建筑面积约430平方米。上海第四批优秀历史建筑名录4M044同列泰晤士报社别墅和美丰银行别墅。这里选取区规划资源局具名照片里的2号楼，从草坪观看它的中央屋坡、窗下红砖墙和右手柱廊。[打开三维模型](../../../cypress-hotel-2-dormer-and-loggia.html) · [区局照片与说明](https://www.shcn.gov.cn/col7698/20261106/1320246.html) · [资料和许可](SOURCES-LICENSE.md)

## 瓦坡与双扇老虎窗

中央屋面分行铺橙瓦。老虎窗有独立的木框、内凹玻璃和悬挑薄顶，左窗下端可见一片浅色，右扇的窗框向前探出。稍低的右侧屋面止于高山墙，窄窗开在两片瓦坡之间。从斜上方可查看两片屋面的交接处。[屋面取点](measurements/roof-tile-courses.json) · [瓦坡模型](study-views/valley.jpg)

照片原幅1028 × 686。用中央二楼两扇窗的八个角点拟合相机，窗心名义间距取1.44米。另在屋面六列无遮挡处量取五十条可辨的瓦行暗缝，估计相邻瓦行沿坡相距约0.31米。墙厚、老虎窗外挑量、暗处的构造和开扇角度均由单幅照片估计。[砖墙窗洞](measurements/second-storey-openings.json) · [相机和尺度](measurements/lawn-camera.json)

另以五列未参与拟合的原照位置检出47条暗缝。46条能与近、远网格的独立瓦唇逐条对应，最大投影偏差约0.85个原始像素。余下一条恰逢两片相邻瓦之间的窄缝，向左右各移0.1像素都能遇到对应瓦唇。实际视角下，部分下唇被前面的瓦片遮住。[瓦行近景及测量示意](study-views/measured-roof-courses.jpg) · [原照片留验点](measurements/unseen-roof-joints-photo.json) · [三档网格比较](measurements/unseen-roof-joints-geometry.json)

## 草坪柱廊

照片中能辨出两个浅拱。沿原图横向测量，净跨约为50和54个像素，拱顶较起拱处抬高约6至8个像素。模型将孔洞切穿，前方方柱、台板、栏杆和后方窗分开建造。两端柱脚在照片中被植物遮住，模型顺着可见直边延至估算地面。后墙用素色墙面补齐阴影中的遮挡部分。[双孔及栏杆测量](measurements/loggia-arch-and-railing-pixels.json) · [模型实景](study-views/arches.jpg)

饭店3号楼的具名地图点落在底图建筑1678内。饭店东侧还有多处建筑，2号楼的外轮廓与草坪立面的端点仍待总平面核实，模型独立展示。[2号与3号楼的地图证据](measurements/hotel-building-sites.json)

## 文件与重建

模型页可下载原始、近景、远景 GLB 及具有七个相机的 Blender 工程。网页下载使用的矿物颗粒纹理由程序生成。原建筑照片作为研究依据。[模型与资料的许可](SOURCES-LICENSE.md)

```sh
python source/build_model.py --output cypress-2.glb
python source/build_model.py --lod --output cypress-2-lod.glb
python source/build_model.py --blender blender --out ./exports --audit ./audit
```

原照可以从区规划资源局的图片链接取得。把环境变量 `CYPRESS_LAWN_PHOTO` 设为原图路径，依次运行 `measurements/measure-window-returns.py`、`measurements/register-lawn-camera.py`、`measurements/measure-roof-courses.py`，即可重算窗洞和瓦行记录。[照片原始地址及 SHA-256](measurements/sources-and-identity.json)
