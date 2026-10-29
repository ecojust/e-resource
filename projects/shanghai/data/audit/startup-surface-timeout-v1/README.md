# 可选通用贴图挂起导致场景无法进入

旧版在 `createShanghaiScene` 返回前等待12张通用材质图片，图片请求没有截止时间。若其中一个请求一直不完成，后续城市建筑目录和模型加载不会开始。若此前外部Overture请求已失败，加载面板会一直保留“建筑服务暂不可用，已切换 OSM”，掩盖真正等待的贴图。

`before.json` / `before-mobile.png`：针对已发布版本a09337c，用真实Chromium阻断Overture，并令12张通用贴图请求挂起。35秒后应用未就绪，加载面板仍显示该提示。

`after.json` / 两张修正版截图：使用相同发布页和真实远程资产，只通过Playwright替换 `architectural-material.js` 为本次修正版，记录其SHA-256。手机故障场景验证10秒贴图截止后仍显示52,312面的金山卫城楼和周边建筑；桌面正常场景验证12张通用贴图全部加载。没有伪造模型或目录响应。

三个单元测试覆盖正常加载/重复清理、单张永久挂起/迟到资源清理、显式失败/其余资源清理。相关灯光与模型资源测试也通过。

该修复处理已复现的初始化阻塞，不证明用户报告必由这一原因触发；仍待具体出错网址和浏览器信息。其他网络请求、地图或WebGL故障不在本次修复范围。超时的图片请求本身不能由Three TextureLoader取消，因此迟到图片到达后会立即释放纹理；不会在运行中的场景补装不完整贴图。

复验：`node --test projects/shanghai/tests/architectural-material-timeout.test.mjs`。安装Playwright与Chromium后，从仓库根运行本目录 `repro-before.cjs` 和 `qa-browser.cjs`，会重写本目录证据。
