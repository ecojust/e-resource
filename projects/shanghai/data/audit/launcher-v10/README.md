# v10启动包：松江方塔单点运行记录

应用提交`50b8becaa8d0e3de125c38c64a3de730e89465ea`；ZIP为75,129,522字节，SHA256 `1cae35145591aafbec74d0fb3d226461c69d2240d60e3855db33f8a2640557b3`，严格低于100 MB。实际归档包含14项本地导航模型、13项流式导航模型；数量来自该ZIP实际manifest/导航及归档报告。底图、全城和流式模型需要联网，资源固定到这一应用提交，不是全城离线包。

生产运行时仅批准`src/realistic-lighting.js`一项阴影修复，其余运行时保持冻结字节；实际ZIP与解压目录逐件核对。[运行时差异](../precise-buildings-v10/two-districts/runtime-fix/runtime-delta.json) SHA256 `6a415603a7e183f868f57607e58471bbd56649f9ec90cff1f130b93af0a87ea2`，修复后运行时SHA256 `6cb2fb4dc1cca564d70f2718014c11600ba5846915df4d707caa5b56a873838c`。

[归档记录](archive-check.json)核对实际ZIP CRC、成员原字节、文件大小和解压结果。[公开应用字节](public-app-proof.json)核对同一应用提交及最终计划的实际响应。两栋独立模型各自发布提交的实际四资产响应分别保留在[方塔](public-models/songjiang-fangta-pagoda.json)、[真如](public-models/putuo-zhenru-main-hall.json)记录中；这些记录不替代公开ZIP下载响应核验，也不把不同提交说成同一HTTP检查。

[解压后运行报告](browser/browser.json)只实际加载**松江方塔**完整模型并拍1图；27项导航、8栋普通精模、6个目录宏的计数来自元数据。完整GLB为19.92 MB，SHA256 `3e7e718d6eb795cebb1e28ab848f021baf482e8a5560a2cbb88ccd8634e864fd`，浏览器实际读取应用提交的固定URL。14个源邻楼保留，截图前后目标OSM组件状态、残余层与事务均实际核对；未整组删除同source ID下的其他组件。

[root视觉记录](browser/visual-review.json)绑定同一ZIP、应用提交及报告，并实际查看[这一张图](browser/songjiang-fangta-pagoda-extracted-smoke.png)。ZIP没有重跑另一栋、所有27项导航、LOD切换、目录生命周期、16区或设备帧率。应用本身的共享11图和两份各5图另见[模型及应用范围](../precise-buildings-v10/two-districts/README.md)。

CDP仅定向阻断已知Overture服务以观察真实OSM回退，生产超时和缓存策略保持。[模型包绑定](package-record.json) · [单点脚本](tools/launcher-smoke.py) · [实际源组件](tools/representative-osm-target-evidence.json)。本整理器只读取已有证据，没有再次运行浏览器或网络。
