# v6.1：07／09与普通民宅222接入

本轮接入三套已经单独发布的模型，使当前HTML达到20栋：15栋外滩、4栋陆家嘴、1栋青浦普通小楼。[武康路129号](../../source/precise/xuhui-wukang-129/DELIVERY.md)已有独立GLB／Blender下载但未接入HTML或通过网页场景验收，不计入20栋。各建筑证据、细化和照片采样范围不同；本轮不是全市测绘或全城逐栋摄影测量。

## 本轮模型和来源

| 建筑 | 可见结构 | 照片采样与限制 |
|---|---|---|
| 7号大北电报公司大楼 | 四层3＋5＋3窗轴、真实洞口、铁门、金属顶帽、后排屋顶窗及中央三角顶 | 6窗18片玻璃，Suicasmo2025 CC0；其余窗/雕饰、后部和顶帽深度含推定 |
| 9号轮船招商局大楼 | 真实开放外廊、不同柱式、石券放射缝、阳台角柱、南侧连续搭接瓦 | 南短翼2窗20片玻璃，Suicasmo2025 CC0；廊深1.85m、后坡和小构件仍为估计 |
| 青浦北大街222号前楼 | 三开间木廊、木格、门叶、灰瓦搭接、字牌与简化双狮 | 只有中央草书匾映射钉钉2022 CC BY-SA 4.0；右门为估计玻璃材质，Fayhoo2016 CC BY-SA 3.0仅辅助结构核对 |

07／09采用冻结OSM／Overture轮廓。222采用Overture的Zenodo／East Asian Buildings原轮廓，底层Qian Shi等CC BY 4.0、聚合ODbL，不能伪造OSM way；门牌、相邻226、街桥和照片支持唯一身份。只替换已确认的源对象，不按半径删除邻楼。

## 实际文件

| 建筑 | 网页GLB | 原始GLB | Blender原生 | 远景GLB |
|---|---:|---:|---:|---:|
| 7号大北电报 | [14,586,648](../../assets/models/bund/web/bund07.glb) | [27,912,424](../../assets/models/bund/bund07.glb) | [43,867,948](../../assets/native/bund/bund07.blend) | [2,991,244](../../assets/models/bund/lod-v4/bund07.glb) |
| 9号轮船招商局 | [30,117,188](../../assets/models/bund/web/bund09.glb) | [76,875,072](../../assets/models/bund/bund09.glb) | [42,678,476](../../assets/native/bund/bund09.blend) | [8,429,340](../../assets/models/bund/lod-v4/bund09.glb) |
| 北大街222号 | [8,560,920](../../assets/models/precise/14-13701-6700/qingpu-beidajie-222/web.glb) | [18,154,244](../../assets/models/precise/14-13701-6700/qingpu-beidajie-222/raw.glb) | [29,405,268](../../assets/native/precise/14-13701-6700/qingpu-beidajie-222/model.blend) | [6,466,884](../../assets/models/precise/14-13701-6700/qingpu-beidajie-222/lod.glb) |

表中均为实际文件字节，逐项核对当前SHA并严格小于100,000,000字节；不是JPEG解码内存或GPU预算。07／09的raw/web嵌入原图，LOD不带图；222的raw/web/LOD均含一张中央匾照片，LOD为91,246三角形。相应作者、EXIF、expected_images与许可继续保留，不能整包称CC0或MIT。

## 城市替换和街道

全市基线保持1,796,419建筑及部件要素、1,708宏块、169,320近景分块，仍有126处有源屋顶和401处父体残余。历史计算1,796,116−98＋401=1,796,419不重新减去v6动态模型。两批v6共6目标，受影响4个near中55要素＝6目标＋49邻要素；222自己的near是1目标＋27邻要素。细模实际可见才隐藏相应普通表示，退出/清单重置恢复归属，不把原实体墙留在真窗洞背后。

07／09前新增317.9618㎡有界铺装，v6追加累计1,162.4622㎡；首批05／06／14与v5铺装、街道家具、树障碍、源孔洞保留。铺装面积、顶面高程、窄缝和材料尺度是模型估计。当前入口为项目`tools/build_bund_street.py`；旧street/build_street.py单独运行只得历史基线。

## 本轮实际验证与边界

本轮三栋HTML技术检查通过，共15组采集、6份近／远景资产核验；root实际查看10张截图并接受有限接入表现。另有独立目录检查：生产20项静态记录复用，以及仅测试响应移除222后的19项动态加入／退出／返回和索引SHA失败保留基线。目录另经root实际图像复核，包含动态退出后返回的叠楼回归视图。三栋静态采集与运行时修复后的回归范围分别记录，不把旧图冒充全部修复后重跑；这不重跑全部20栋或全城逐栋核验。 见[完整报告](../audit/precise-buildings-v6/release-next/README.md)。222远景虽实际查看，但楼体太小／被周边遮挡，不能独立评价立面；LOD存在、字节和三角形由技术报告验证。

网页技术检查与root逐图视觉复核分别记录，目录静态复用及受控动态加入也分开记录。报告中的warning、预期取消和外部网络事件仍原样保留；不把无shader/page/required-asset错误写成无warning。截图与模型SHA绑定，不以旧单体native通过替代当前HTML验收。

[首批v6报告](REALISM_V6.md)保留其05／06／14的15组采集、10张有限视觉核对和后续旧启动包05冒烟范围；[v5报告](REALISM_V5.md)保留全市生成/抽样解码/浏览器范围。本轮报告不扩张这些历史验证。

[上一版17栋在线预览](https://rawcdn.githack.com/ecojust/e-resource/ac388a7c598b81af3b6ac9fc79d4b63ee59a3ad4/projects/shanghai/index.html#mode=walk)（固定ac388…应用，尚不是本轮20栋页面）。[上一版v6启动包](../../downloads/shanghai-web-launcher.zip)为74.99 MB／74,988,136字节、按需联网；它在本地包含原14栋并联网加载首批3栋。**本轮20栋新预览与ZIP尚待发布，旧链接不能当作新增三栋已上线的证据。**

## 重建和未完成部分

[外滩源码](../../source/bund/photo-rebuild-v6/README.md)与[普通楼源码](../../source/precise/README.md)保留冻结输入、离线构建器、原图作者和逐栋推定说明。照片保留拍摄时光影，不是去光照PBR；没有照片支持的背立面、内部房间、精细雕刻和全市真实门窗仍未完整复原。所有绝对尺寸和局部后退估计按各包说明理解，不以数值小数冒充测量精度。
