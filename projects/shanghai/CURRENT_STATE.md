# 当前交付状态 · 宝山孔庙大成殿 v15

[全部32处地标目录](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/landmarks.html) · [最新第三人称漫游](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#mode=walk) · [宝山大成殿直达](index.html#landmark=baoshan-confucian-dacheng-hall&mode=walk)

本轮新增宝山孔庙大成殿，已接入第三人称漫游并通过模型与本地网页验收。目录现有32处独立直达链接：15栋外滩、4栋陆家嘴和13栋逐栋复原建筑。建筑普通精模目录涉及11个宏块；源替换登记18项，涉及12个宏块和16个近景分块。

本栋按单独的大成殿来源替换，保留相邻8栋建筑。模型包含双层曲瓦顶、独立瓦垄与斗栱、三组透空格扇、三段后白墙、环廊及前平台石栏、御路石。它曾用作陈化成纪念馆，2015年修缮后改作大成书院；本项目名称保持“宝山孔庙大成殿”，不混同旁边另一栋纪念馆。

## 模型文件

| 文件 | 字节 |
|---|---:|
| [原始GLB](assets/models/precise/14-13721-6684/baoshan-confucian-dacheng-hall/baoshan-confucian-dacheng-hall-raw.glb) | 29,752,792 |
| [网页GLB](assets/models/precise/14-13721-6684/baoshan-confucian-dacheng-hall/baoshan-confucian-dacheng-hall-web.glb) | 11,876,292 |
| [远景GLB](assets/models/precise/14-13721-6684/baoshan-confucian-dacheng-hall/baoshan-confucian-dacheng-hall-lod.glb) | 2,939,940 |
| [Blender](assets/native/precise/14-13721-6684/baoshan-confucian-dacheng-hall/baoshan-confucian-dacheng-hall.blend) | 14,479,200 |

四件文件均严格小于100,000,000字节，实际字节与SHA256已核对。[模型元数据与哈希](source/precise/baoshan-confucian-dacheng-hall/model-metadata.json) · [可编辑源码与说明](source/precise/baoshan-confucian-dacheng-hall/README.md)

## 实际验收范围

本栋原始与解码后网页模型的几何、材质对应及Blender重新打开检查通过。完整模型389,128三角形、远景107,808三角形，三件GLB均无照片纹理或外部缓冲依赖。

本地浏览器11项检查通过：32处目录链接唯一，新增入口按登记起点初始化，完整模型／远景切换、离开18km后释放及返回完整模型、精确来源替换、8栋邻楼保留、真实W键行走约0.42m及松键后停止。35件运行时文件保持原字节。审核者实际查看正面、背面、远景和返回行走后4张网页截图。[完整检查与实际图像复核](data/audit/precise-buildings-v15/baoshan-confucian-dacheng-hall/README.md)

本轮没有重新遍历其余31栋模型的所有视角，未验证可游览室内、全部动态目录组合或手机GPU帧率；本地浏览器结果不等于发布后公共网页HTTP检查。

## 资料与精度

上海市文旅推广网提供朝向、屋顶、环廊和0.48m栏凳等资料；知识贝壳转载《上海辞典》的公开节录记载15.45×11.42m、总高13m和室内净高11.5m，未标明原书版次或宽深测量边界。模型采用约13m名义约束，实际网格包络高约12.95m；这不是本项目实测高度。底图约18.38×15.63m也不能直接当成精确墙线。

这是有照片参照的外观模型，尚非照片级真实复原，未进行现场测绘或摄影测量。侧山墙、隐蔽木构、兽饰和龙纹为推估，表面风化简化；楹联没有伪造未辨清的字句。三间／五间文献口径差异保留，部分近视角上檐会遮挡匾牌上部。

参考照片已实际查看正面、背面及侧廊。公开参考图为Fayhoo的2014年正面照（CC BY-SA3.0），其旧“陈化成纪念馆”横匾不代表现代状态；许可未明的其他照片只供研究，不加入公开包。模型不嵌入照片像素。

[官方建筑介绍](https://www.meet-in-shanghai.net/cn/shanghai-cultural-relics-protection-unit/baoshan-confucius-temple-dacheng-hall-843867/) · [辞典公开节录](https://zsbeike.com/cd/45460125.html) · [Commons参考照片](https://commons.wikimedia.org/wiki/File:Kongmiao_Dachengdian.jpg)

全市16区底图仍在，1,796,419个建筑及部件尚未全部逐栋照片复原；本轮新增一栋，不能代表全市精细建模完成。地图及远程模型需要联网，加载超时可刷新页面。

下载ZIP仍为v13，75,198,283字节，SHA256 `409cf1070eb6625c9d2d5cb6c4929739bc2e0b925916de42a5463378274c8976`；不包含v14导航改进和v15宝山模型。[旧启动包](downloads/shanghai-web-launcher.zip) · [其实际验证范围](data/audit/launcher-v13/README.md)。

## v14导航与v13模型交付（历史保留）

以下原文完整保留；其“当前”、数量和验证状态均指对应历史版本。

# 当前网页状态 · 地标直达更新

[全部31处已建模地标直达](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/landmarks.html) · [最新第三人称漫游](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#mode=walk)

本次更新导航：增加完整地标目录和显式入口；点击建筑直接进入漫游；支持当前页面内更换地标链接；打开某栋建筑的链接时直接从该建筑的已有漫游起点初始化。仓库首页的旧版固定预览链接已替换为跟随master的最新入口。

覆盖31处已建模目的地：15栋外滩建筑、4栋陆家嘴地标、12栋逐栋复原建筑。全市16区地图保留。模型与此前v13相同，最新建筑为杨浦区图书馆；此次没有新增或修改模型及已核验的漫游起点。

[验证记录](data/audit/navigation-v14/README.md)。提交署名为agent；本次每个文件严格小于100,000,000字节。网上历史固定提交链接不会自动升级，请收藏上方最新入口。

下载ZIP仍为v13（75,198,283字节），需要联网，不包含本次导航改进；使用本次功能请打开最新网页。以下为模型及ZIP上一版交付信息。

## 模型与ZIP交付 · v13


本轮新增杨浦区图书馆整馆模型，覆盖历史旧体、扩建长翼、现代角部和两处内院。已接入上海第三人称漫游，应用提交 `387561d8a7297eb7fc2a42907f0819fa1d61e958`。[模型、预览与来源](source/precise/yangpu-library/CURRENT_STATE.md)。

当前精选导航 31 项、普通精模 12 栋、目录 10 个宏块；源建筑替换登记 17 项，涉及 11 个宏块和 15 个近景分块。保留全市 16 区地图；1,796,419 个建筑及部件要素尚未全部完成逐栋照片复原。

本栋四件模型：原始 GLB 20,564,732 字节、网页 GLB 6,622,720 字节、远景 GLB 2,217,772 字节、Blender 10,088,881 字节，均严格低于 100,000,000 字节。31 件运行时文件保持 V12 字节；近景、LOD、返回和真实 W 行走的[网页验收范围](data/audit/precise-buildings-v13/yangpu-library/README.md)单独记录。

启动包 75,198,283 字节，SHA256 `409cf1070eb6625c9d2d5cb6c4929739bc2e0b925916de42a5463378274c8976`；14 项本地模型、17 项联网模型，固定到上述应用提交。307 件归档成员通过完整 CRC/SHA 校验；冒烟过程中实际按请求解压 77 件文件并逐件核对 SHA。从实际 ZIP 按请求解压的目录启动，加载固定提交上的杨浦图书馆完整模型，核对 1 张截图；同时检查目录采用、源建筑替换及同块邻居。 [下载](downloads/shanghai-web-launcher.zip) · [实际启动包验证范围](data/audit/launcher-v13/README.md)。

未进行现场测绘或摄影测量。西侧、北侧和内院部分窗跨、局部尺寸及饰纹按有限资料推估；屋脊总高不等同于审批图中的 18.49m 檐口高度。 软件渲染截图不代表用户设备帧率。本轮只新增这一栋整馆，并非全市逐栋精细建模全部完成。

使用时需要联网。若完整模型读取超时，请刷新页面重新加载；当前没有自动重试。
