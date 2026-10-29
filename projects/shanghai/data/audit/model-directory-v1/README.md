# 统一模型目录网页接入验证

公开版本：[全部模型与地标](https://rawcdn.githack.com/ecojust/e-resource/da9d3f3561ce3b77dd378aa96c6de1a2140d9056/projects/shanghai/landmarks.html)。首次访问若出现 githack 提示，点击 **Open the page**。

本次将六个独立候选及16区地面水系展示入口接入统一目录，并更新根目录、项目 README 与 latest.html。城市漫游仍为原有38个入口；没有修改候选几何、坐标、源替换登记、碰撞或行走状态。

- `local-browser.json`：本地 Chromium 从目录逐项点击进入六个候选及水系页面；六个候选均加载 full / LOD，与清单三角面数量声明匹配且有渲染帧；水系默认黄浦区加载成功。
- `public-browser.json`：上述检查在公开固定版本重新执行，未拦截或替换网络资源；页面异常和同版本 HTTP 失败均为空。
- 两份报告同时覆盖桌面名称／行政区搜索、无结果、分组锚点清除筛选、390×844 手机搜索与横向溢出、禁用 JavaScript 后45个普通链接仍存在。
- `local-directory-*.png`、`public-directory-*.png`：桌面及手机目录截图。
- `bindings.json`：本次目录源码、目录清单、生成器及相关测试的字节数与 SHA-256。

相关检查：

```bash
node --test tests/landmark-directory.test.mjs
python tools/build_landmark_directory.py --check
python tools/restoration_progress.py --check
node data/audit/model-directory-v1/qa-browser.cjs http://127.0.0.1:8000/ /tmp/model-directory-review
```

五项目录测试通过。README 还核对了38个地标锚点、53个相对链接和64个唯一预览 URL 的路径映射。本次实际联网逐项测试的是统一目录与七个独立展示页，不是重新验收38处城市漫游或全部城市模型。

六个候选仍明确标为未接入城市原址；不能把这次网页目录接入当作地理定位、源对象替换或真实行走验收。模型原有的照片、尺寸估计及局部建模范围仍以各自来源说明为准。
