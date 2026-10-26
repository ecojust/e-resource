# v10：松江方塔与真如寺大殿

生产运行时仅有明确批准的`src/realistic-lighting.js`阴影修复，使不透明的`Inferred dark glazing`可投射阴影；其余运行时文件保持冻结字节。运行时差异SHA256 `6a415603a7e183f868f57607e58471bbd56649f9ec90cff1f130b93af0a87ea2`，修复后文件SHA256 `6cb2fb4dc1cca564d70f2718014c11600ba5846915df4d707caa5b56a873838c`。[实际差异](../../data/audit/precise-buildings-v10/two-districts/runtime-fix/runtime-delta.json)。

本版应用提交`50b8becaa8d0e3de125c38c64a3de730e89465ea`，导航27项、逐栋普通精模8栋、目录6个宏块。[实际验收](../../data/audit/precise-buildings-v10/two-districts/README.md)包括两栋共享11张静态图和两个新宏分别5张目录图；范围限定于记录的模型、视点与加载过程。

方塔采用九级四面、八层上部回廊的构成，分别构造曲檐瓦片、栏杆、斗栱、贯通壸门和镂空九相轮。42.65m总高与底层砖身6m为文献名义值；42.5m、48.5m等口径差异保留。另记塔刹7.85m、塔心木13m及露出8.20m不相互冒充同一测量。下廊对称构造、层高、收分及不可见处含估计；有限脊座中心带接触检查不扩大为全宽连续贴合或全塔无碰撞证明。[方塔原始说明](../../source/precise/songjiang-fangta-pagoda/README.md)。

真如大殿依据三间三进、十六柱及其现代可见门窗构成建模。整体高度约10.24m为模型估计，公布的158m²没有明确测量口径，不等于已取得精确墙线。文献柱高、直径和侧脚须按原记录理解，未把天王殿的尺寸套入大殿。照片中后方塔尖属于另一栋塔，大殿屋顶没有新增该塔尖；天王殿等邻楼保持。现今未见背面和完整室内不声称已核验。[大殿原始说明](../../source/precise/putuo-zhenru-main-hall/README.md)。

两栋原source owner边界完整保留，仅用于身份和精确替换，模型不强拉伸为来源轮廓。观察起点也不等于经过现场确认的入口或公共通行路线。照片按各自实际分辨率和许可保留，可能是Commons预览或原生小图；没有统一声称全分辨率原图，也未将像素嵌入几何模型。

### 松江方塔的5张参考图

| 作者与照片 | 日期 | 许可 |
|---|---|---|
| [Kgbkgbkgb](https://commons.wikimedia.org/wiki/File:Square_Tower_of_Songjiang.jpg) | 2010-01-12 | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0) |
| [Humanclose](https://commons.wikimedia.org/wiki/File:Pagoda_at_Xingshengjiao_Temple.jpg) | 2013-09-01 11:17:10 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) |
| [Heights](https://commons.wikimedia.org/wiki/File:Fangta_Park_Songjiang.JPG) | 2009-08-09 | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0) |
| [Acot一杯茶](https://commons.wikimedia.org/wiki/File:%E6%9D%BE%E6%B1%9F%E5%85%B4%E5%9C%A3%E6%95%99%E5%AF%BA%E5%A1%94.jpg) | 2017-07-28 16:00:57 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) |
| [Acot一杯茶](https://commons.wikimedia.org/wiki/File:%E5%85%B4%E5%9C%A3%E6%95%99%E5%AF%BA%E5%A1%94.jpg) | 2017-07-28 16:20:02 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) |

### 真如寺大殿的4张参考图

| 作者与照片 | 日期 | 许可 |
|---|---|---|
| [ScareCriterion12](https://commons.wikimedia.org/wiki/File:%E4%B8%8A%E6%B5%B7%E7%9C%9F%E5%A6%82%E5%AF%BA%E5%A4%A7%E6%AE%BF2025.8.jpg) | 2025-08-30 10:11:09 | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) |
| [Ukmist](https://commons.wikimedia.org/wiki/File:%E7%9C%9F%E5%A6%82%E5%AF%BA%E5%A4%A7%E6%AE%BF.JPG) | 2013-09-26 13:48:04 | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0) |
| [ScareCriterion12](https://commons.wikimedia.org/wiki/File:%E4%B8%8A%E6%B5%B7%E7%9C%9F%E5%A6%82%E5%AF%BA%E5%A4%A7%E6%AE%BF2019_(1).jpg) | 2019-12-11 15:01:55 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) |
| [Haier7917](https://commons.wikimedia.org/wiki/File:%E7%9C%9F%E5%A6%82%E5%AF%BA3.jpg) | 2009-03-30 | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0) |

实际单楼来源、构建方法和交付清单见各目录README.md、BUILD.md、COPYRIGHT.md及delivery-record.json。原冻结记录的阶段字段保持；当前网页接入状态以[项目当前状态](../../CURRENT_STATE.md)与各栋CURRENT_STATE.md为准。全城尚未逐栋照片复原，软件渲染功能检查不代表用户硬件帧率。
