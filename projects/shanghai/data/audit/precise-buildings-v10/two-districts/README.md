# v10：方塔、真如寺大殿网页接入核对

本版精选导航27项、逐栋普通精模8栋、普通目录6个宏块，新增松江方塔与普陀真如寺大殿。原25条导航与四个既有目录宏保持。生产运行时代码仅有一项明确批准的例外：`src/realistic-lighting.js`使不透明的`Inferred dark glazing`可投射阴影，修复邻楼窗格造成的屋面漏光；其余运行时文件保持冻结字节。本页只覆盖这两栋和记录的加载流程，不表示上海16区已经逐栋照片复原。

[运行时差异](runtime-fix/runtime-delta.json) SHA256 `6a415603a7e183f868f57607e58471bbd56649f9ec90cff1f130b93af0a87ea2`，修复后运行时SHA256 `6cb2fb4dc1cca564d70f2718014c11600ba5846915df4d707caa5b56a873838c`。旧11图虽技术通过，但root视觉退回；本页只依据修复后的新静态和目录报告。

[静态实际报告](static/browser.json)完成11张截图：两栋各自完整模型、斜向细节、远景LOD、返回4图，再做全局释放/返回/重置3图。全局后两图只属于最后的真如大殿，不重复算作方塔的观察机位。root实际逐张查看，[视觉记录](static/visual-review.json)保留每张图的范围与限制。四次实际web/LOD字节审计、23个源邻楼及各楼对应的实际OSM组件检查分别通过。

每个新宏另外完成独立的3阶段/5图检查：静态模型收养；只由目录加载、卸载、返回；故意损坏索引后拒绝精模并保留完整源建筑。每次只移除该宏一栋，因此计数27→26；方塔保留15个原要素，真如保留10个。不能把其中一栋结果代作另一栋验收。

- **松江方塔**：保留14个同近景块邻楼；目录卸载实际释放15个几何对象。网页GLB、原始GLB、LOD、Blender依次为19.92、47.28、9.68、23.97 MB。每件严格低于100 MB。[源码与来源](../../../../source/precise/songjiang-fangta-pagoda/README.md) · [目录实际报告](catalog/songjiang-fangta-pagoda/browser.json) · [5图视觉记录](catalog/songjiang-fangta-pagoda/visual-review.json)。
- **真如寺大殿**：保留9个同近景块邻楼；目录卸载实际释放19个几何对象。网页GLB、原始GLB、LOD、Blender依次为11.91、29.21、8.62、14.82 MB。每件严格低于100 MB。[源码与来源](../../../../source/precise/putuo-zhenru-main-hall/README.md) · [目录实际报告](catalog/putuo-zhenru-main-hall/browser.json) · [5图视觉记录](catalog/putuo-zhenru-main-hall/visual-review.json)。

照片保留各自作者、原字节及许可，模型没有嵌入其像素。方塔名义高度与真如柱尺寸来自各自文献；比例、不可见处、来源轮廓与墙/檐线关系、部分构造仍有估计，不是测绘或摄影测量模型。真如大殿与其后塔、天王殿分别保留，未把后塔尖建在大殿屋脊上。完整限制见各栋原始源码说明和实际视觉记录。

已知Overture域名的CDP故障注入只用于核对真实OSM回退；生产资源超时、缓存策略未改。检查采用软件渲染环境，不是用户设备帧率、所有网络环境或全城照片精度保证。启动包待应用发布后另做档案、公开字节和一次解压后代表楼加载/1图，不重复两套目录生命周期；本页不提前宣称ZIP完成。

[实际输入绑定](release-binding.json)
