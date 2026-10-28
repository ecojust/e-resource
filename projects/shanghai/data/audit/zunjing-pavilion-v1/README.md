# 尊经阁独立候选模型验证

范围：外观候选模型与独立网页，不代表地理接入、测绘精度或历史建筑复原验收。

- geometry.json：原始完整模型342,946三角面，远景62,148三角面。实际解码 Meshopt 后逐三角形比较 float32 顶点坐标一致（统一正负零后比较）；两份模型坐标有限且无零面积三角形。
- native.json：Blender 保存后重新打开，建筑对象顶点和三角面哈希一致；展示用地面、灯光与相机不计入建筑几何。
- browser.json：真实 Chromium 加载与近远景切换、损坏响应保留旧模型、重试、自动距离切换、手机布局测试。复跑需要 Playwright、Chromium 和 projects/shanghai 本地 HTTP 服务，执行 node qa-browser.cjs。
- native-front.png、native-oblique.png、native-rear.png 为原生 Cycles 渲染；browser-desktop.png 和 browser-mobile.png 为网页截图。
- 公用资源释放测试 tests/model-resources.test.mjs 通过。

几何检查脚本位于 source/precise/chongming-zunjing-pavilion/source/verify_geometry.py，输入原始完整/远景模型和 decode_meshopt.mjs 实际解码的文件；不使用图像相似度或自报元数据代替实际几何比较。

照片显示的双层屋顶、南立面门窗分组及匾额可在渲染中辨认。模型材质是均匀色彩，不复现照片中的风化；隐藏立面、雕刻、脊兽和高度存在推定。没有进行全建筑碰撞、结构、室内、全球流形或测绘位置验收。原地物覆盖整个博物馆，因此城市替换仍被明确禁止。

完整模型与远景模型已分别从源码重新生成，输出 GLB 与发布源文件逐字节一致。
