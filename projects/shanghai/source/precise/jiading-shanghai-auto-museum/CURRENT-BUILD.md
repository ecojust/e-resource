# 源码复现与检查

公开源码必须完整保留作者 source-freeze.json 所列59项原相对路径。`references/`中的五张CC参考图、字体轮廓及许可、两张自制设计图、OSM数据和requirements文本均为明确冻结依赖；资产参考目录中的同图副本不能代替作者根目录中的依赖。

在仓库的 `projects/shanghai` 项目目录中执行，输出使用新目录：

```bash
cd source/precise/jiading-shanghai-auto-museum
python -m pip install -r requirements.txt
python run_root.py --verify-only
python run_root.py --raw-output /absolute/new-run/raw
blender -b -t 1 --python render_previews.py -- \
  --glb /absolute/new-run/raw/jiading-shanghai-auto-museum-raw.glb \
  --output /absolute/new-run/native --samples 24 --threads 1
```

原始生成使用Python3.12、NumPy2.3.5和Shapely2.2.0；当前原生图使用Blender4.3.2、Cycles CPU、24 samples和单线程。字形轮廓及局部修复输入随源码提供，正常raw生成不访问网络、不依赖系统字体、MAIN项目或旧v1模型。`prepare_repairs_from_v1.py`只用于可选的历史修复输入再推导；重新执行该诊断需要另备固定SHA的旧raw与sidecar，不能用新raw冒充历史输入。

源码检查和小夹具不能替代实际导出验证。当前证据分别检查闭合/方向/法向、12372旧构件保持、一块面板下表面改动、五个新增连接件、6114项有限问题、5114项玻璃上下边面积接合，以及20条对当前完整不透明候选集合的槽内射线。原始失败与问题映射保持独立，容差没有因为失败而放宽。

Web与LOD使用冻结工具中的gltfpack1.3.0，参数为 `-cc -noq -km -ke`。两者均从完整raw生成，POSITION保留Float32，不执行整楼减面。压缩后须用实际GLTFLoader载入数据验证有向三角位置、材质、法向及有限问题；四项博物馆补充证明通过逐构件实际位置/材质保持显式继承，不能只凭文件尺寸或结构检查宣布通过。

`tools/`保留所选已冻结的源码、数学检查器与依赖锁，`evidence/`记录执行时的绝对路径和SHA。这些是原执行档案，不是可直接跨路径运行的现成审计输入。项目upstream/vendor、Node依赖与gltfpack的WASM按锁另行准备，未把外部二进制重复夹带进作者源码。若重放，需要为新实际输出生成新的描述符与报告；不能改写旧报告SHA、把旧raw证据改名成新证据。模型raw复现与历史审计重放是两个不同范围。

实际原生视觉决定由根审核者对真实PNG给出；注册器仍要求真实解码、完整九节prebrowser审核及显式源码白名单。网页与第三人称漫游另行实际检查。本说明不执行注册、安装或发布。
