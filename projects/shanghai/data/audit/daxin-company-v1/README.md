# 大新公司历史主楼外观交付

[主地图直接查看](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#landmark=huangpu-daxin-company&mode=overview) · [来源与范围](../../../source/precise/huangpu-daxin-company/README.md) · [四资产清单](../../../assets/models/candidates/huangpu-daxin-company/manifest.json)

模型版本已发布为 [`9b0d1af`](https://github.com/ecojust/e-resource/commit/9b0d1afb8bb21b992ef91b11161273c5e40cae2b)。[固定版本主图](https://raw.githack.com/ecojust/e-resource/9b0d1afb8bb21b992ef91b11161273c5e40cae2b/projects/shanghai/index.html#landmark=huangpu-daxin-company&mode=overview)及[线上核对](publication.json)记录14个实际HTTP响应，包括主页面、目录、脚本、清单和四资产，全部与该提交字节一致。随后补入真实Git版本时间，并将两份README正文中的旧汇总数字纳入自动同步；按区表、模型和浏览器代码不变。扩展的下一栋模型增量用例已验证正文与目录一起更新，最终文档检查见[root-checks.json](root-checks.json)。

本件为南京东路830号的大新公司历史主楼外观，包括西南圆弧高转角、南西街面、竖向窗带、顶层敞廊与花格、檐齿、圆片冠饰及雨篷。北侧B馆、东侧C馆、跨街连接、室内和商业广告不并入本件。北东隐面与内部屋顶采用简化估计；单体交付不表示整个商业中心完成。

## 来源与估计

[文献复核](documentary-review.json)实际取得《上海名建筑志》大新公司章节，记十层、高42.3米、占地3667平方米、1936年1月10日开业。高度测量端点和完整平面未给出；名录的1934年建造年代不能改写成该章节已经确认的竣工时间。

[照片复核](photo-review.json)实际查看四张西南街景，明确其属于同一方向族，不能当作四面覆盖。现代外观以2025年照片为主要观察依据；北面、东面、屋顶及内院没有可靠照片核准。参考照片不作为纹理、不随模型分发，作者和许可见来源登记。

文献42.3米作为作者选择的高部最大标高，不表示该数字已测至模型冠饰。楼层分配、窗轴、退距和屋顶厚度含估计；地图旧楼源约3068平方米与文献占地不相等，不强行缩放或吞并相接楼。

## 模型和定位证据

| 资产 | 字节 | 三角面 |
|---|---:|---:|
| 原始GLB | 9,961,448 | 183,288 |
| 网页GLB | 3,158,656 | 183,288 |
| 远景GLB | 1,062,040 | 53,372 |
| 可编辑Blender | 5,324,631 | 183,288（建筑网格） |

四件共19,506,775字节，每件小于100 MB，实际外包约55.337×57.859×42.300米。[几何检查](geometry.json)和[打包检查](packaged.json)核对实际序列化几何、3815／2185个分别闭合且正体积的作者构件，以及每档21条实际表面射线。凹窗、入口、2米廊后墙、2.3米后玻璃、弧顶窗、冠部开孔与实体正控均通过；实际Meshopt解码后的网页及远景GLB与各自原始几何逐材质有向三角面一致。

[原生检查](native.json)实际重开Blender，建筑网格与源GLB一致，摄影棚不计入建筑；GLB和Blender均无照片纹理。[独立审查](independent-model-review.json)另行解码三档、核对外包和五个高度截面，并用15条独立射线检查凹窗、入口、退廊、四个弧顶窗及冠孔。

[正面](native-front-v2.png)、[斜面](native-oblique-v2.png)、[北东估计面](native-rear-v2.png)和[冠饰／退廊细部](native-crown-gallery-detail-v2.png)均已实际查看，记录见[native-visual-review.json](native-visual-review.json)。最终v2补齐照片可见的宽浅色阶梯竖带和真弧顶窗；原始试作图保留私有，没有混入最终图像证据。

[定位复核](footprint-review.json)绑定旧主楼唯一源 `building / ca6dccd6-0c72-4376-8978-e6e660629037`，宏块 `14-13720-6694`、localId2372；原点约121.47027548、31.23702544，朝向−15.35035407°。北侧B馆和东侧C馆是独立源，建造年代未核；范围划分不以假定年代为依据。近景块与B馆共享GLB，必须按源身份裁剪，不能整块移除。

三档实际水平外包一致，0.86米有界配准余量涵盖作者墙体内退与地图边界差异，再与旧楼唯一源相交，精确使用原源3068.024平方米作替换范围，残余为0。B/C馆及其他邻源与模型、碰撞及裁剪范围均无交集；北侧模型净距约0.515米，碰撞净距约0.335米。此为完整独立旧楼的外观候选，不代表整个商业中心。定位记录另含实际远近景解码，确认共享块内旧楼与B馆的独立源身份和屋顶几何。

[增量接入检查](global-integration-checks.json)的6项检查确认旧32条候选记录和历史审计不变、替换仅限旧楼唯一源、向量源残余为0、其他源ID不受影响，裁剪三角形由66增至73／128。[运行时检查](runtime-checks.json)另含33项当前目录灯牌／镜头测试；生产脚本保持原字节。[生成及导航检查](root-checks.json)包括12项实际目录与导航测试，覆盖资产清单路径和主图直达。

本轮库存核验只读取新四资产，继承前轮冻结证据；累计35份清单、140件文件和512,661,557字节。目录生成另沿用既有两件派生廊道资产检查，没有重跑历史模型全量资产矩阵。

[真实浏览器检查](browser.json)一次完成六张截图，全部经过[逐图实际查看](browser-visual-review.json)：[近景](browser-auxiliary-desktop-full-59457ce2-8e3f8c1c.png)、[远景](browser-auxiliary-desktop-lod-59457ce2-8e3f8c1c.png)、[手机模型页](browser-auxiliary-mobile-full-59457ce2-8e3f8c1c.png)、[主图桌面](browser-global-default-desktop-29494443-8e3f8c1c.png)、[主图手机](browser-global-default-mobile-29494443-8e3f8c1c.png)、[320像素下73个灯牌](browser-beacons-320-city-73-29494443-8e3f8c1c.png)。默认西南方向、35°俯角能完整显示主楼；B/C楼体仍在，独立屋顶投影点及源身份记录用于辅助核对。近远景实际切换、四资产下载字节和SHA、73个主图导航入口均通过。

窄屏73张编号牌均可见、无重叠，中心命中正确；原生触控编号73后从新新切换到大新，地址片段、名称、地图中心和模型可见状态均改变。全程使用一个Chrome页面，窗口尺寸和城市加载完成后再取证；无失败重试，控制台错误、警告和HTTP失败均为零。

## 目录和 TODO

当前按区目录为73处入口、16区，黄浦区25处；40处原有入口保留室外漫游，33件候选提供近似定位的全局俯瞰。两份README中的模型查看入口均进入 `projects/shanghai/index.html`。35份候选资产清单包含两份早已登记的模型，不能当作35个新增地图入口。

[TODO与目录检查](todo-directory-checks.json)核对27项已交付任务和46项既有库存退出活动制作列表；历史主楼重复制作任务共移除8条，原始1058条名录保留，活动建筑／构件及调查线索剩1050条。具名源按图层和ID精确关联18条，剩1018条待查。新新的北侧旅馆、天井与连接继续保留；下一制作项为长乐路109号华懋公寓／锦江饭店锦北楼。

## 重建与复验

从仓库根目录执行，Python依赖见[source/requirements.txt](../../../source/precise/huangpu-daxin-company/source/requirements.txt)，另需Blender和gltfpack：

```sh
python projects/shanghai/source/precise/huangpu-daxin-company/source/build_model.py --out /tmp/daxin-build
python projects/shanghai/source/precise/huangpu-daxin-company/source/build_model.py --out /tmp/daxin-build --lod
blender -b -t 4 --python projects/shanghai/source/precise/huangpu-daxin-company/source/build_native.py -- --raw /tmp/daxin-build/huangpu-daxin-company-raw.glb --out /tmp/daxin-build/huangpu-daxin-company.blend --previews /tmp/daxin-native --samples 16 --suffix=-v2
python projects/shanghai/source/precise/huangpu-daxin-company/source/package_assets.py --raw /tmp/daxin-build/huangpu-daxin-company-raw.glb --lod /tmp/daxin-build/huangpu-daxin-company-lod.glb --native /tmp/daxin-build/huangpu-daxin-company.blend --out /tmp/daxin-assets --gltfpack /path/to/gltfpack
python projects/shanghai/source/precise/huangpu-daxin-company/source/verify_geometry.py --assets /tmp/daxin-assets --out /tmp/daxin-packaged.json --gltfpack /path/to/gltfpack --blender /path/to/blender
python projects/shanghai/tools/build_candidate_city_integrations.py --check
python projects/shanghai/tools/build_model_todo.py --check
python projects/shanghai/tools/build_landmark_directory.py --check
python projects/shanghai/data/audit/daxin-company-v1/todo-directory-checks.py
```

浏览器脚本[qa-browser.cjs](qa-browser.cjs)需Playwright、Chromium及提供项目和稀疏资产的HTTP服务。设置 `NODE_PATH`、`MODEL_BASE_URL` 和 `CHROMIUM_PATH` 后执行 `node projects/shanghai/data/audit/daxin-company-v1/qa-browser.cjs --run`。只使用一个浏览器页面；更换窗口尺寸后，等待DOM、画布、地图内部尺寸与界面布局连续两帧稳定，城市楼块加载完成后再检查实际显示。
