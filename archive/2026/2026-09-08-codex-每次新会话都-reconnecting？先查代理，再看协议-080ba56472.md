---
url: "https://x.com/Liu_zhongxisn/status/2059664137748410850"
title: "Codex 每次新会话都 Reconnecting？先查代理，再看协议"
author: "Drunk @Liu_zhongxisn"
source: "x_bookmark"
date: 2026-09-08
chars: 1874
images: 1
---

# Codex 每次新会话都 Reconnecting？先查代理，再看协议

装完 Codex Desktop 之后，每次开新会话，第一句话发出去，界面就开始转圈。

左下角弹 reconnecting，一次、两次，有时候五次。等它自己连回来，又能正常答了。你换过模型，重启过 App，甚至怀疑是不是账号被风控了——都不是。

能用，但新会话的第一句话总要抖几下。你刚想让 Codex 改个文件，它先给你表演一段 reconnecting，节奏全乱。

我排查下来就两种情况。一种是 Codex 根本没走到代理。另一种是代理走了，但 WebSocket 那条链路在本地代理上扛不住。

这两个长得像，修法不一样。很多人一上来就去改 config.toml，其实可能只是 Codex 没吃到代理环境变量。也有人只配了 .env，新会话第一次还是重连——因为代理对 WebSocket upgrade 或长连接保持的处理就是不太行。

## 先判断是不是这类问题

下面这些如果全中，那大概率是这篇要说的：

- Codex Desktop 能正常登录。

- 模型能用，不是所有请求都失败。

- 每次新会话第一条消息容易 reconnecting。

- 重连几次之后又能正常回。

- 你电脑上跑了 Clash、Shadowrocket、sing-box、Surge、V2RayN 之类的本地代理。

- 代理端口是 7890、10808、7897，或者你自己改过的。

这种情况先别怀疑模型。模型真不可用的时候表现很直接：请求直接报错、鉴权失败、模型列表拉不出来、所有对话都走不下去。你现在看到的是"新会话第一下抽风，后面又好了"，这更像是连接建立阶段的稳定性问题。

如果日志里出现了类似这样的东西，那基本坐实：

proxy(http://127.0.0.1:10808/) intercepts 'https://chatgpt.com/'
tunneling HTTPS over proxy

请求确实过了本地代理。问题就在这条链路上。

![Article image](/assets/2026-09-08-codex-每次新会话都-reconnecting？先查代理，再看协议-080ba56472/01.jpg)

## 第一步：让 Codex 明确吃到代理

最轻的方案，在 .codex 目录下放一个 .env 文件。

路径：

macOS: /Users/你的用户名/.codex
Windows: C:\Users\你的用户名\.codex

Windows 上直接在资源管理器地址栏敲 %USERPROFILE%\.codex 也能到。

进去以后新建文件，名字就叫 .env。不是 .env.txt——Windows 默认隐藏文件扩展名，这个坑踩过的人不少。不确定的话就打开"查看文件扩展名"，或者用 PowerShell 看一眼。

里面写两行：

HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890

端口换成你自己的。比如有些 Windows 代理工具本地端口是 10808：

HTTP_PROXY=http://127.0.0.1:10808
HTTPS_PROXY=http://127.0.0.1:10808

保存，然后完全退出 Codex Desktop 再重开。不是关窗口就完了——确认后台进程也没挂着。这类环境变量是启动时读的，App 已经开着的时候你补 .env，它不一定立刻认。

开一个新会话，发一句短的话试一下。如果 reconnecting 消失或者明显变少，就别继续折腾了。问题就是 Codex 没拿到代理配置。

## 配了代理还是抖？

Codex 已经在走代理了，但新会话第一次建立流式连接还是连续 reconnecting。这时候就不是"没代理"的问题，而是"代理链路对某种连接方式不稳"。

尤其是 WebSocket。

WebSocket 本身没问题。但你的请求要先过本地代理、再过系统代理、走 HTTPS 隧道、做协议升级、最后才能建成长连接——中间这么多环节，随便哪一个晃一下，你界面上看到的就是 reconnecting。

而且它还不是每次都挂。第一次连接最容易出事，后面稳定了又跟没事一样。有点像车打火——冷车的时候拧钥匙要吭哧好几下，热了之后一下就着。这种最迷惑人。

## 哪些情况别按这篇修

- 完全登录不了的——不是这篇。

- 所有请求都失败的——不是这篇。

- 代理工具自己都访问不了 chatgpt.com 的——先修代理，别动 Codex。

- 公司网络、防火墙、安全软件直接拦截 Codex 的——.env 和 HTTP/SSE provider 也未必救得回来。

这篇只解决一个很具体的场景：Codex 能用，但新会话第一次请求总要 reconnecting 几次。

这种情况，先配 .codex/.env，确认它真的走了代理。
