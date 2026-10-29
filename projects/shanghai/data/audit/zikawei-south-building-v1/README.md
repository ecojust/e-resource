# 徐家汇藏书楼南楼外观候选核验

模型为五开间、三层外廊和阁楼的南楼；相邻北楼不在模型内。以公开照片为依据，尺寸、后翼屋面和未见立面为估计，未接入城市原址或计入完成建筑数。年代资料冲突保留于来源说明。

- `source-files.json` 绑定源码、来源照片、材质、模型和网页；资产 manifest 记录文件大小与 SHA-256。
- `geometry.json`：原始与 Meshopt 解码后的完整/远景三角面一致，无退化或重复索引三角面。
- `pbr.json`：位置、UV、三张原创贴图一致。
- `structure-full.json`、`structure-lod.json`：每档22项外廊、老虎窗、楼板和屋面探测；故意封堵外廊/老虎窗的负例均被拒绝。
- `native.json`、`native-geometry.json`：Blender重新打开后的150,176面及几何、UV和嵌入图片匹配；原生渲染另附。
- `reproduction.json`：重建原始GLB、远景GLB与材质逐字节一致。
- `source-context.json`：源身份与7个周边源建筑的保守平面检查。未发现邻居重叠，但模型外挑部分超出源面；不代表地面、碰撞或行走验收。
- `browser.json`：实际 Chromium 近远景、自动切换、损坏远景恢复、移动端尺寸及材质检查。截图为实际网页渲染。

复现构建见 [源码说明](../../../source/precise/xuhui-zikawei-south-building/README.md)。本地网页核验：启动项目目录HTTP服务后执行 `node data/audit/zikawei-south-building-v1/qa-browser.cjs`。公开核验使用 `ZIKAWEI_PUBLIC_URL` 指定固定提交预览地址执行 `qa-public.cjs`，结果另存 `public.json`。

目录搜索、390像素手机布局及点击新入口实际加载模型，见 `directory-local.json`；公开版本使用同一 `qa-directory.cjs` 验证并保存 `directory-public.json`。
