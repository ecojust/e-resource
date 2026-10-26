# 照片相机入口

`photo_camera.py` 只在已加载的原生模型上设置相机与渲染参数，不导入或改造建筑，不使用look-at重新瞄准。它首先校验 `photo-camera-lock.json` 绑定的 camera、calibration、geometry、原JPEG和raw的bytes/SHA；进入Blender时还校验通用native转换报告的rawSHA、nativeSHA及建筑mesh数量。

普通Python先执行：

```bash
python photo_camera.py --check --width 1500 --report output/photo-camera-check.json
```

已通过34点检查，包含A/B/D不同立面及后退屋顶；ENU→Blender相机与标定P投影差小于1.3e-12px。错误套用glTF轴的负对照产生约1591px偏差。检查不启动Blender，也不代表照片外形已验收。

在统一的Blender队列中，可使用本包未改的转换器副本：

```bash
blender -b --python common/blender_finish.py -- \
  --glb output/xuhui-wukang-129-raw.glb --output native --render \
  --view-azimuth 307.69525847124856 --view-elevation 12 \
  --width 1500 --height 1000

blender -b native/xuhui-wukang-129-raw.blend --python photo_camera.py -- \
  --width 1500 --render native/photo-camera.png \
  --report native/photo-camera-run.json
```

需要保存另一个透视相机native时才追加 `--save-blend native/photo-camera.blend`。不保存也能完成渲染与报告。默认读取已加载 `.blend` 同目录下的 `原stem-blender.json`；如果报告另置，可使用 `--native-report /path/to/report.json`。`--raw` 可指向独立资产目录，但内容必须符合锁定SHA。

原照片1800×1200，整像素中心坐标；缩图使用 `(p+0.5)*scale-0.5`。脚本正确保留fx/fy差异，并把pixel-aspect两值规范到均不小于1，避免Blender属性截断。执行前还用真实 `world_to_camera_view` 再核4点，允许数值误差不超过0.02px。任何实际Blender检查和最终渲染结果归parent运行报告所有，本准备任务没有调用Blender。

正交推荐azimuth307.695258°来自源临街外法线，elevation12°；它用于形体概览，不等同于拟合照片相机。照片相机保留原矩阵中的roll/pitch。

预览地面注意：raw最低z=−0.11m是入地拱门灰套，源地坪仍为z0。通用转换器会以最低点放预览地板，可能在−0.135m；parent可仅调整Preview_only地板到约−0.01m，建筑/raw不变。相机脚本本身不移动地板。

精简SOURCE清单不携带生成的raw和native。离线运行 `build_model.py` 后会重建锁定raw，之后即可执行相机检查；原图、控制点、固定helper与构建环境记录均保留。
