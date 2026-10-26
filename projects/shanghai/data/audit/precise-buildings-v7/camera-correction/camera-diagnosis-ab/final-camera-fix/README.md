# 两项实际镜头问题的最小候选

仅隔离stage；没有改main/candidate或重新生成模型。root真实MVT诊断确认：旧眼点位于对街1148内，强制重算虽请求5.04m镜头，22.5缩放上限仍让实际眼点留在楼内。两处上限临时设24后，实际zoom22.946909370320537，眼点匹配请求、collisionAt返回null，对街悬空窗框消失。该诊断近景裁掉屋顶，不能代替新导航/完整A/B视觉验收。

候选保留现有碰撞规则，只补源缓存revision与双重缩放上限：

1. scene真正重建collision cache后递增revision，沿用850ms节流。
2. controller静止早退检查revision；计算结果未变时不重复jumpTo，防止moveend触发的重建反馈。显式reset仍提交。
3. 共享`WALK_CAMERA_MAX_ZOOM=24`用于Map构造和setCameraFromTo；普通overview setCamera仍保留原范围。

精确安装白名单仅四个项目相对路径，见`installation-plan.json`：

- `src/walk-controller.js`
- `src/map-scene.js`
- `tests/camera-collision-revision.test.mjs`（目标必须不存在）
- `package.json`（仅给原完整npm链加入新测试）

每项必须核对计划中的旧SHA/新SHA，root受控安装；不要递归复制payload，里面vendor symlink/旧walk-controller测试仅用于本地验证，不在白名单。原文件在`base/`保存。实际runtime diff见`camera-fix.patch`。

新增测试正常运行只引用项目相对src/vendor，1148小几何fixture内联并注明宏/localID/源表SHA，不依赖私有stage、冻结基线、外网或浏览器。6项通过：晚到/移除轮廓、静止缓存/节流/同camera无反馈、显式reset、旧adapter兼容、真实vendored MapLibre5.04m与3.5m请求不能再被双重22.5夹住。原源码负控4项失败；原walk-controller suite通过。

```sh
node --test tests/camera-collision-revision.test.mjs
```

root安装后再跑一次完整npm以及新候选的完整11capture流程。旧qa-ab失败报告、原profile及原截图必须保留。无需增加碰撞半径、修改邻楼、改变全城数据或运行Blender。本候选没有声称任意分辨率/硬件性能或全市完全精确碰撞。
