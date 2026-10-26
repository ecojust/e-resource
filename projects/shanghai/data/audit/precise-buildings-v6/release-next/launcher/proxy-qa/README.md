# 启动包真实网络验收：显式环境代理副本

此目录是原 `next/ordinary-launcher/browser-catalog.py` 和两份probe的精确复制后，仅添加测试环境代理接线。原脚本、两份原probe、ZIP、解压应用均未修改。原两probe在此也逐字节相同。

`proxy-only.patch` 是全部脚本差异，`source-comparison.json` 绑定原/新SHA。逻辑门槛、三阶段、远程原字节SHA校验、截图和失败处理均不放宽。读取 `HTTPS_PROXY`，缺失时读取 `HTTP_PROXY`；没有环境代理则明确失败。代理传入实际 `browser.new_context(proxy=...)`，让浏览器网络、`context.request` 与 `route.fetch` 使用同一代理。`localhost,127.0.0.1` 显式绕过代理。

报告的 `network` 只记录环境变量名、协议、主机、端口、bypass及是否提供凭据，不记录用户名、密码或原始环境值。实际环境为 `http://proxy:8080` 且无凭据。`NODE_OPTIONS` 改DNS排序不能替代代理；该副本不依赖它。

root执行（只运行一个浏览器）：

```sh
python /workspace/shanghai_expansion/building-by-building-v6/next/launcher-release/proxy-qa/browser-catalog.py \
  --url http://127.0.0.1:8874/shanghai_expansion/building-by-building-v6/next/launcher-release/extracted/shanghai/ \
  --output /workspace/shanghai_expansion/building-by-building-v6/next/launcher-release/browser-catalog-proxy \
  --timeout-ms 240000 --width 1040 --height 760 --dpr 1
```

无浏览器预检已通过：`check_proxy_catalog.py` 使用真实 Playwright `APIRequestContext` 和同一proxy选项访问固定提交catalog，实际HTTP200、689字节、完整SHA与解压包descriptor一致；同一context访问本地registry也为HTTP200且字节完全相同。见 `api-preflight.json`。这不是完整浏览器通过证据，不代表其余资源全部可用。真实浏览器仍须完成三阶段及root目视复核，所有网络/校验失败照常保留，不mock响应成功。

纯配置5项检查见 `proxy-configuration-tests.json`；未重复运行模型/全城/旧32项测试。原 direct/IPv4失败目录继续保留。
