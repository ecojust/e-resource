# 当前状态

生产运行时仅有明确批准的`src/realistic-lighting.js`阴影修复，使不透明的`Inferred dark glazing`可投射阴影；其余运行时文件保持冻结字节。运行时差异SHA256 `6a415603a7e183f868f57607e58471bbd56649f9ec90cff1f130b93af0a87ea2`，修复后文件SHA256 `6cb2fb4dc1cca564d70f2718014c11600ba5846915df4d707caa5b56a873838c`。[实际差异](data/audit/precise-buildings-v10/two-districts/runtime-fix/runtime-delta.json)。

v10应用提交`50b8becaa8d0e3de125c38c64a3de730e89465ea`；精选导航27项、逐栋普通精模8栋、目录6个宏块。[松江方塔](https://rawcdn.githack.com/ecojust/e-resource/50b8becaa8d0e3de125c38c64a3de730e89465ea/projects/shanghai/index.html#landmark=songjiang-fangta-pagoda&mode=walk) · [真如寺大殿](https://rawcdn.githack.com/ecojust/e-resource/50b8becaa8d0e3de125c38c64a3de730e89465ea/projects/shanghai/index.html#landmark=putuo-zhenru-main-hall&mode=walk) · [两栋实际模型与网页证据](data/audit/precise-buildings-v10/two-districts/README.md)。

ZIP为75,129,522字节，SHA256 `1cae35145591aafbec74d0fb3d226461c69d2240d60e3855db33f8a2640557b3`。完成实际归档/解压校验、两栋独立发布模型与应用公开响应字节核对，以及解压后**松江方塔一次完整模型加载和1图**；[ZIP记录](data/audit/launcher-v10/README.md)。包含14项本地导航模型、13项流式模型，需联网。ZIP没有重测另一栋、全部27项导航、LOD或目录生命周期、16区及设备帧率。

方塔42.65m采用文献名义总高，层间比例、檐出和隐藏构造仍有估计；真如大殿总高及屋面尺度为模型估计，文献158m²口径未明，不能当作实测墙体尺寸。源建筑轮廓用于身份及精确替换，不证明墙线、檐线或台基范围。两栋每个raw/web/LOD/Blender及ZIP均严格小于100,000,000字节。v9及更早正文保留为历史；全城仍未逐栋达到照片复原精度。
