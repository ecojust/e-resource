# 上海现代建筑精细模型与应用验收 v11

本批次将上海汽车博物馆和包玉刚图书馆接入上海漫游场景。最终应用包含 29 个导航点、10 条精细建筑目录记录、8 个目录区域；替换登记覆盖 15 个独立源建筑、9 个区域和 13 个近景块。原有 27 个导航点、六个目录区域及其既有数据保持一致。

| 建筑 | 源区域 | 唯一替换对象 | 保留的同块邻居 |
| --- | --- | --- | --- |
| 上海汽车博物馆 | 14-13706-6691 | 870 | 735, 797 |
| 包玉刚图书馆 | 14-13718-6705 | 201 | 35, 60, 299, 333, 375, 466, 947 |

## 实际浏览器与视觉审核范围

静态测试实际完成 11 张截图，root 逐张查看。测试强制使用 OSM；其中 8 个指定近景捕获在截图前后分别核验对应的实际 MVT 组件及零残留。远景、卸载等其余截图按各自原合同检查，不能将近景组件结论扩展到所有截图或全市建筑。

[静态实际报告](static/browser.json)：940941 B；SHA-256 `fae5b47be9d9c8bdac3ad19c50bab445118991737cc27edf1f3b316ec3574500`。

[静态 root 视觉审核](static/visual-review.json)：6795 B；SHA-256 `3c25b67d986ec70c615e61a04dee2f44e2c1dbac39972bf9b51386d3f4b2c096`。

两个新区域分别完成静态接管、仅动态加载、损坏索引拒绝三阶段，以及各自五张实际截图和 root 视觉审核。测试包括加载、返回、卸载释放、源对象恢复与坏索引零模型请求。

目录测试使用每次捕获时实际启用的建筑主源，**没有强制 OSM**。下表主源取自实际 `source.buildingSource`，不是探针的 `source=openmaptiles`。`overture` 下的 `inactive/null` 表示 OSM 未启用、组件检查为空，是原目录合同允许的分支；无指定替换目标的卸载或拒绝阶段也可能记录 `active/null`。这些状态不构成该目录帧的 OSM 组件证明。OSM 组件证明来自前述独立强制 OSM 静态测试。

| 建筑 | 实际目录截图 | 建筑主源 | OSM 截图前 / 后状态 |
| --- | --- | --- | --- |
| 上海汽车博物馆 | [static-jiading-shanghai-auto-museum-loaded.png](catalog/jiading-shanghai-auto-museum/static-jiading-shanghai-auto-museum-loaded.png) | `overture` | `inactive/null/inactive/null` |
| 上海汽车博物馆 | [static-jiading-shanghai-auto-museum-returned.png](catalog/jiading-shanghai-auto-museum/static-jiading-shanghai-auto-museum-returned.png) | `overture` | `inactive/null/inactive/null` |
| 上海汽车博物馆 | [dynamic-jiading-shanghai-auto-museum-loaded.png](catalog/jiading-shanghai-auto-museum/dynamic-jiading-shanghai-auto-museum-loaded.png) | `overture` | `inactive/null/inactive/null` |
| 上海汽车博物馆 | [dynamic-jiading-shanghai-auto-museum-returned.png](catalog/jiading-shanghai-auto-museum/dynamic-jiading-shanghai-auto-museum-returned.png) | `overture` | `inactive/null/inactive/null` |
| 上海汽车博物馆 | [dynamic-jiading-shanghai-auto-museum-index-hash-rejected-baseline-visible.png](catalog/jiading-shanghai-auto-museum/dynamic-jiading-shanghai-auto-museum-index-hash-rejected-baseline-visible.png) | `overture` | `inactive/null/inactive/null` |
| 包玉刚图书馆 | [static-minhang-baoyugang-library-loaded.png](catalog/minhang-baoyugang-library/static-minhang-baoyugang-library-loaded.png) | `overture` | `inactive/null/inactive/null` |
| 包玉刚图书馆 | [static-minhang-baoyugang-library-returned.png](catalog/minhang-baoyugang-library/static-minhang-baoyugang-library-returned.png) | `overture` | `inactive/null/inactive/null` |
| 包玉刚图书馆 | [dynamic-minhang-baoyugang-library-loaded.png](catalog/minhang-baoyugang-library/dynamic-minhang-baoyugang-library-loaded.png) | `overture` | `inactive/null/inactive/null` |
| 包玉刚图书馆 | [dynamic-minhang-baoyugang-library-returned.png](catalog/minhang-baoyugang-library/dynamic-minhang-baoyugang-library-returned.png) | `overture` | `inactive/null/inactive/null` |
| 包玉刚图书馆 | [dynamic-minhang-baoyugang-library-index-hash-rejected-baseline-visible.png](catalog/minhang-baoyugang-library/dynamic-minhang-baoyugang-library-index-hash-rejected-baseline-visible.png) | `overture` | `inactive/null/inactive/null` |

[上海汽车博物馆目录实际报告](catalog/jiading-shanghai-auto-museum/browser.json)：414174 B；SHA-256 `f9da4ffcac265bd6f9264a66dde02ea4cca50971c26e9ca4e9df037871bff44e`。

[上海汽车博物馆目录 root 视觉审核](catalog/jiading-shanghai-auto-museum/visual-review.json)：3679 B；SHA-256 `43df87d36e86ebb415f02dec9f216e0af0f307e4b1b2b924471cffe6e708b869`。

[包玉刚图书馆目录实际报告](catalog/minhang-baoyugang-library/browser.json)：420471 B；SHA-256 `a2f1ddf51b9b12e80dada046bcc6b0a1e6b1f81251cb8c2f4f79e17745deb6c5`。

[包玉刚图书馆目录 root 视觉审核](catalog/minhang-baoyugang-library/visual-review.json)：3991 B；SHA-256 `b7a5bc3a789ad6aaab880c65b5612313c4826295b383b8a69af588fa24fd8899`。

## 模型文件与来源

以下文件大小以 MB 显示，大小与 SHA-256 来自最终实际交付文件；每个文件均严格小于 100 MB。几何按公开参考资料制作，建筑高度、层间尺寸及照片推断部分属于建模估计，不是测绘实测。

| 建筑 | 用途 | 文件 | 大小（MB） | SHA-256 |
| --- | --- | --- | ---: | --- |
| 上海汽车博物馆 | raw | [jiading-shanghai-auto-museum-raw.glb](../../../../assets/models/precise/14-13706-6691/jiading-shanghai-auto-museum/jiading-shanghai-auto-museum-raw.glb) | 31.95 | `fcaf6c3ec778a4edc6d4c335aedea02472b8ddff24013d2e555f09e949eebd5f` |
| 上海汽车博物馆 | web | [jiading-shanghai-auto-museum-web.glb](../../../../assets/models/precise/14-13706-6691/jiading-shanghai-auto-museum/jiading-shanghai-auto-museum-web.glb) | 10.35 | `ef7480db922f0e40dde0d5ad34332e41c63c24033bbc147a6d76067318c91cf9` |
| 上海汽车博物馆 | lod | [jiading-shanghai-auto-museum-lod.glb](../../../../assets/models/precise/14-13706-6691/jiading-shanghai-auto-museum/jiading-shanghai-auto-museum-lod.glb) | 10.35 | `ef7480db922f0e40dde0d5ad34332e41c63c24033bbc147a6d76067318c91cf9` |
| 上海汽车博物馆 | native | [jiading-shanghai-auto-museum.blend](../../../../assets/native/precise/14-13706-6691/jiading-shanghai-auto-museum/jiading-shanghai-auto-museum.blend) | 14.65 | `3bd8e9edfabfd33ef6387a1f117e8773baab3aaa981194ace118eace2dad994c` |
| 包玉刚图书馆 | raw | [minhang-baoyugang-library-raw.glb](../../../../assets/models/precise/14-13718-6705/minhang-baoyugang-library/minhang-baoyugang-library-raw.glb) | 23.89 | `abea24f7c9df46d07aa44837c99a5ecc8a631ca5595a0881854f4334c035c982` |
| 包玉刚图书馆 | web | [minhang-baoyugang-library-web.glb](../../../../assets/models/precise/14-13718-6705/minhang-baoyugang-library/minhang-baoyugang-library-web.glb) | 7.84 | `e78ae366679a2c9d4b1894bb401c72f96027176c947a8a019ba0eeace506d5fa` |
| 包玉刚图书馆 | lod | [minhang-baoyugang-library-lod.glb](../../../../assets/models/precise/14-13718-6705/minhang-baoyugang-library/minhang-baoyugang-library-lod.glb) | 1.36 | `617b8f15ba391702245f16f2d1b2207ad875405c9e1174fbbd0acb971244b2f4` |
| 包玉刚图书馆 | native | [minhang-baoyugang-library.blend](../../../../assets/native/precise/14-13718-6705/minhang-baoyugang-library/minhang-baoyugang-library.blend) | 12.69 | `a4870d73e61e8c83fe4326f3f1508a601ba2aceb0046e5ecb49f59456942ecb1` |

汽车博物馆 web 与 LOD 都保留 528,396 个三角形；LOD 使用相同几何的压缩交付，没有声称几何减面。包玉刚图书馆 web 为 442,088 个三角形，作者指定 LOD 为 52,864 个三角形；减去细小接缝并保留受检结构与开口，实际解码和补充证据记录在交付元数据中。

- [上海汽车博物馆源码说明](../../../../source/precise/jiading-shanghai-auto-museum/README.md)；[实际交付元数据](../../../../source/precise/jiading-shanghai-auto-museum/delivery/model-metadata.json)。
- [包玉刚图书馆源码说明](../../../../source/precise/minhang-baoyugang-library/README.md)；[实际交付元数据](../../../../source/precise/minhang-baoyugang-library/delivery/model-metadata.json)。

源建筑采用原冻结坐标和独立唯一归属，邻居及源细片按对应证据保留。公开源码与参考图片各按随附许可和白名单交付；未将私人研究图片作为贴图或源码公开。

## 保留范围与限制

本次应用沿用既有 31 个运行时文件，绑定清单 SHA-256 为 `139c5291e476029c2a11ef3523985140722a87a210fabc69b327d77a7e223b39`。本页只汇总实际模型、静态和目录验收，不新增运行时代码变更或重新解释旧报告。此时 ZIP 提取运行及最终公开应用字节核验各由后续独立实际报告说明，本页不宣称它们已通过。

这两个建筑的验收不代表全上海已经完成照片级复刻，也不构成硬件帧率、精确测绘、所有入口可通行或所有视角无差异的保证。源资料身份、估计范围及各次人工视觉审阅限制保留在链接的原报告中。
