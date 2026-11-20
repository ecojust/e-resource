# 圣三一基督教堂（独立钟塔与连接短廊）

九江路219号院内，站在东侧花园面向教堂，钟塔位于主堂右侧。四跨短廊从主堂北侧柱廊通向塔脚。法国国家图书馆收藏的正面老照片同时拍到塔脚的两座低窗、上方中窗、钟室下的小券列和连接短廊。1908年出版的全景也可看到独立方塔、成对高钟窗与四座小尖顶。[主堂研究](../huangpu-holy-trinity-cathedral/README.md) · [1908年景](https://commons.wikimedia.org/wiki/File:Tcitp_d381_the_shanghai_anglican_cathedral.jpg) · [照片、署名与拍摄记录](reference-review.json)

主堂于1869年开放，钟塔其后兴建。Scott家族资料记1893年完成，Darwent经《Victorian Web》转引记1901年奠塔基。旧塔尖在1966年被毁，2006年照片的台顶仍然平整。主管机构记2007年启动教堂修缮；2015年日景和2026年夜照均可见恢复后的砖红色尖塔，具体竣工日待核。主管机构列现塔尖高48米；Darwent记旧塔尖105英尺，约32米。现模型沿用48米总高。[基督教全国两会](https://www.ccctspm.org/churchinfo/396) · [Scott家族档案整理](https://gilbertscott.org/holy-trinity-cathedral-shanghai/) · [Darwent记载](https://victorianweb.org/art/architecture/scott/39.html)

方形塔身依次建出底层、小拱列、成对的尖券钟窗和顶栏。百叶之间留有空间；方形台上有四座角部小尖塔，八角基座的四面凸窗位于中央长尖以下，尖顶带浅色石环和金属风向标状端饰。各层标高、材色、百叶节距和砖皮层次均依照片估计。塔内钟具和楼梯、被邻房遮挡的低位细节，以及相邻学校旧楼另待调查。[2006年的平顶方塔](https://commons.wikimedia.org/wiki/File:圣三一堂.JPG) · [2015年尖塔俯视](https://commons.wikimedia.org/wiki/File:Shengsanyi_Jidujiaotang.JPG) · [2026年图片](https://commons.wikimedia.org/wiki/Category:Holy_Trinity_Cathedral_(Shanghai))

市房屋管理局2023年公布的第一批优秀历史建筑名录将本建筑列为 **1A025**，原名“圣三一基督教堂”，表内现名“黄浦区政府礼堂”，地址九江路201号。现宗教机构公布的联系地址为九江路219号。门牌沿用的年代有别，院内主堂和钟塔按照片与地图轮廓分别定位。[市房管局首批名录](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [主管机构现行地址](https://www.ccctspm.org/)

## 成品与检查

[三维查看器](../../../holy-trinity-bell-tower.html) · [地图定位](../../../index.html#landmark=huangpu-holy-trinity-bell-tower&mode=overview) · [下载清单与哈希](../../../assets/models/candidates/huangpu-holy-trinity-bell-tower/manifest.json)

| 文件 | 十进制 MB | 字节 | 三角面 |
| --- | ---: | ---: | ---: |
| [原始 GLB](../../../assets/models/candidates/huangpu-holy-trinity-bell-tower/huangpu-holy-trinity-bell-tower-raw.glb) | 2.679 | 2,679,216 | 50,384 |
| [网页 GLB](../../../assets/models/candidates/huangpu-holy-trinity-bell-tower/huangpu-holy-trinity-bell-tower-web.glb) | 0.927 | 927,264 | 50,384 |
| [远景 GLB](../../../assets/models/candidates/huangpu-holy-trinity-bell-tower/huangpu-holy-trinity-bell-tower-lod.glb) | 0.561 | 561,052 | 28,880 |
| [Blender 源文件](../../../assets/models/candidates/huangpu-holy-trinity-bell-tower/huangpu-holy-trinity-bell-tower.blend) | 0.774 | 774,356 | 50,384 |

原始、网页与远景三份GLB各通过42项钟窗、百叶间隙、尖顶、角塔、四跨短廊及塔门的射线检查。Blender重开95个可编辑网格并按材料核对完整表面。城市原体616在塔基范围内局部截断；原近景保留65.88%，独立测得地面障碍49.13平方米。[全景](../../../data/audit/holy-trinity-bell-tower-v1/huangpu-holy-trinity-bell-tower-preview.png) · [上部钟室](../../../data/audit/holy-trinity-bell-tower-v1/bell-stage.png) · [连接廊](../../../data/audit/holy-trinity-bell-tower-v1/connecting-arcade.png) · [逐图复核](../../../data/audit/holy-trinity-bell-tower-v1/author-visual-review.json) · [三种网格的实测](../../../data/audit/holy-trinity-bell-tower-v1/surface-checks.json) · [近远景原体与地面范围](../../../data/audit/holy-trinity-bell-tower-v1/placement-geometry.json)

## 定位与重建

塔心约在主堂东墙中点往本地X方向24.0米、Y方向9.6米，发布原点为东经121.4818356862、北纬31.2386747705。X轴方位343.41°，Y轴朝西偏南253.41°。方台边长估计6.4米，短廊从塔心X−11.80米接到塔身X−3.20米，横向宽约4.30米。官网上方照片可区分小塔、草坪与旧校楼，局部边界留有米级配准误差。[主管方图文、上方照片及地图来源](reference-review.json)

在仓库根目录执行以下命令。环境需要 Python 3、NumPy、Shapely 2.1、Node、gltfpack 0.25、Blender 4.3、ImageMagick 7及Open Image Denoise 2.5。工具路径可用 `--gltfpack`、`--blender`、`--oidn` 传入。主堂的尖券、柱廊与坡屋面构造在此复用，源代码哈希见参考记录。

```sh
python -B projects/shanghai/source/precise/huangpu-holy-trinity-bell-tower/source/build_model.py \
  --out /tmp/tower-assets --audit /tmp/tower-audit
```

原创几何及代码采用仓库 MIT 许可。照片研究来源按各权利人署名，未写入纹理或发布模型。地图衍生数据遵循各自许可。[MIT许可](../../../../../LICENSE) · [来源登记](reference-review.json)

独立页在1250×820桌面和390×844手机上完成近远景切换，四项下载的字节和哈希与清单一致。[浏览器实测](../../../data/audit/holy-trinity-bell-tower-v1/viewer.json) · [截图复核](../../../data/audit/holy-trinity-bell-tower-v1/viewer-visual-review.json)
