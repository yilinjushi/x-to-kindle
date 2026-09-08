---
url: "https://x.com/wadezone/status/2056907392068231597"
title: "0成本教你开 giffgaff eSIM，保姆教程，有手就行"
author: "Koda @wadezone"
source: "x_bookmark"
date: 2026-09-08
chars: 4823
images: 12
---

# 0成本教你开 giffgaff eSIM，保姆教程，有手就行

现在想在国内搞一张 giffgaff 卡，最麻烦的地方不是注册账号，而是“开卡成本”被越抬越高。

你如果走实体 SIM，通常要等国际邮寄，时间不稳定；找代开，又要付代开费，还得把账号、验证码、支付环节交给别人，风险也高。

更尴尬的是，国行 iPhone 本身不支持 eSIM。很多人看到这里就以为这条路断了。

其实没断。

这篇我讲一个几乎 0 成本的办法：不用买实体卡，不找人代开，只用电脑里的安卓模拟器，自己把 giffgaff eSIM 开出来。

关键点是：

你不需要先让国行 iPhone 支持 eSIM。

你只需要先拿到 giffgaff eSIM 的激活码。

模拟器只是开卡工具，不是最终使用设备。

![Article image](/assets/2026-09-08-0成本教你开-giffgaff-esim，保姆教程，有手就行-8aea7729cd/01.jpg)

## 这套方法到底在做什么？

一句话：

→ 用电脑模拟一台支持 eSIM 的安卓手机
→ 让 giffgaff App 认为设备支持 eSIM
→ 然后在 App 里购买 eSIM，拿到激活码

完整链路是：

→ 电脑
→ → MuMu 安卓模拟器
→ → Root
→ → Magisk / 面具
→ → LSPosed
→ → HookEuicc
→ → giffgaff App
→ → 购买 eSIM
→ → 拿到激活码
→ → 后续安装 / 下发

注意：模拟器只是用来开卡。

eSIM 开好之后，不是只能用在模拟器里。

模拟器的作用是绕过 giffgaff App 的设备检测，拿到激活码。

真正使用 eSIM，要看你后面把激活码安装到哪里：

- 支持 eSIM 的手机
- eSIM 转接方案
- 9esim 这类下发方案
- 其他支持 eSIM 的设备或工具

如果你是国行 iPhone，仍然不能原生添加 eSIM，但可以继续走转接或下发方案。

## 开始前准备

你需要准备 5 样东西。

1. 一台电脑

建议 Windows。

这套流程依赖安卓模拟器、Root、Magisk、LSPosed。Windows 上成功率更高，也更容易排查。

2. 一个 giffgaff 账号

没有账号先注册。

如果你想走上车链接，可以用这个：

Get your giffgaff SIM here, with a reward when you join.

https://giffgaff.com

3. 一个可用支付方式

后面购买 / 充值 giffgaff eSIM 会用到。

4. 一个稳定海外网络

尤其后面如果用 9esim 下发 eSIM，建议开全局英国节点。

不要只开浏览器代理，要保证模拟器 / 下发工具也走同一个网络环境。

5. giffgaff 工具包

工具包下载：

→ http://mega.nz/file/XAEhkDxI

解密密钥：

→ YuHRzhbB_W15NB1J9DFt-y1LaQrCRZxV5UBPKnY2fLg

工具包里要用到这些东西：

- MuMu 模拟器：在电脑里创建安卓手机环境
- Magisk / 面具：提供 Root / 模块能力
- LSPosed：让 Hook 模块作用到指定 App
- manager.apk：LSPosed 管理器入口
- HookEuicc：让 giffgaff 识别设备支持 eSIM
- Via 浏览器：处理登录 / 跳转更稳
- giffgaff App：购买 eSIM、拿激活码

![Article image](/assets/2026-09-08-0成本教你开-giffgaff-esim，保姆教程，有手就行-8aea7729cd/02.jpg)

安全提醒：

这套方案涉及 Root 和 Hook，不是官方推荐路径。

不要在模拟器里保存主力账号、重要隐私、长期银行卡信息。

## Step 1：安装 MuMu 模拟器

先解压工具包。

找到 MuMu 安装程序，运行安装。

安装时会联网下载大约 900MB 的系统文件。

装好后打开 MuMu。

如果界面不是中文，先把语言改成中文，后面会少很多误操作。

![Article image](/assets/2026-09-08-0成本教你开-giffgaff-esim，保姆教程，有手就行-8aea7729cd/03.jpg)

这一关的验收标准：

→ MuMu 能正常打开
→ 能进入模拟器管理界面

不要急着装 giffgaff。

真正关键的是后面这台安卓设备有没有 Root、可写系统盘和模块能力。

## Step 2：新建一台安卓设备，并打开 Root

在 MuMu 里新建一台设备。

建议选择竖屏手机。

创建完成后，先不要启动。

先进入设备设置，打开两个关键选项：

→ 磁盘：可写系统磁盘
→ 其他：手机 Root 权限

![Article image](/assets/2026-09-08-0成本教你开-giffgaff-esim，保姆教程，有手就行-8aea7729cd/04.jpg)

这一步是地基。

如果这里没做好，后面会出现这些问题：

- Magisk 装不上
- LSPosed 不生效
- HookEuicc 没反应
- giffgaff 仍然提示不支持 eSIM

你可以这样理解：

→ 没有 Root，就没有 Hook
→ 没有可写系统盘，Magisk 就很容易装不进去

这一关的验收标准：

→ 设备已创建
→ 可写系统磁盘已开启
→ Root 权限已开启

## Step 3：把工具包放进模拟器

启动刚才创建的设备。

先把安卓系统语言改成简体中文。

然后打开 MuMu 顶部的“更多工具”，找到共享文件夹。

把工具包复制进共享文件夹。

再回到模拟器，用系统文件管理器打开共享文件夹，就能看到工具包。

![Article image](/assets/2026-09-08-0成本教你开-giffgaff-esim，保姆教程，有手就行-8aea7729cd/05.jpg)

如果你在模拟器里看不到工具包，按这个顺序排查：

→ 是不是复制到了当前设备的共享文件夹？
→ 文件管理器有没有刷新？
→ 有没有重启模拟器？
→ 是不是开了多个模拟器实例，放错目录了？

这一关的验收标准：

→ 模拟器文件管理器里能看到工具包
→ 能看到 Magisk / LSPosed / HookEuicc / giffgaff 等安装包

## Step 4：安装 Magisk / 面具

在模拟器里打开工具包。

安装 Magisk，也就是“面具”。

第一次打开时，系统可能会弹 Root 授权。

选择：

→ 永久记住
→ 授予 Root 权限

然后在 Magisk 里选择：

→ 直接安装到系统

如果一开始没看到这个选项，就退出 Magisk，重新打开。

![Article image](/assets/2026-09-08-0成本教你开-giffgaff-esim，保姆教程，有手就行-8aea7729cd/06.jpg)

安装完成后，重启模拟器。

重启后再次打开 Magisk，确认它能正常运行。

这一关的验收标准：

→ Magisk 能打开
→ Magisk 拿到了 Root
→ Magisk 可以从本地安装模块

如果 Magisk 装不上，优先回到 Step 2，检查 Root 和可写系统盘。

## Step 5：安装 LSPosed

打开 Magisk。

进入：

→ 模块 → 从本地安装

选择工具包里的 LSPosed 框架包。

安装完成后，手动重启模拟器。

![Article image](/assets/2026-09-08-0成本教你开-giffgaff-esim，保姆教程，有手就行-8aea7729cd/07.jpg)

这里有一个很容易卡住的坑：

重启后，通知栏不一定会出现 LSPosed 入口。

如果你看不到入口，不要一直等。

直接这样做：

→ 解压 LSPosed-v1.9.2-7024-zygisk-release.zip
→ 找到 manager.apk
→ 在模拟器里安装 manager.apk
→ 手动打开 LSPosed 管理器

这一关的验收标准：

→ LSPosed 已作为 Magisk 模块安装
→ 模拟器已重启
→ LSPosed 管理器能打开

## Step 6：安装 HookEuicc、Via、giffgaff

接下来安装三个应用：

→ HookEuicc
→ Via 浏览器
→ giffgaff App

先装 HookEuicc。

然后打开 LSPosed：

→ 模块 → HookEuicc → 开启模块 → 作用域里勾选 giffgaff

![Article image](/assets/2026-09-08-0成本教你开-giffgaff-esim，保姆教程，有手就行-8aea7729cd/08.jpg)

注意：

“装了 HookEuicc”不等于“HookEuicc 对 giffgaff 生效”。

必须同时满足：

→ HookEuicc 已安装
→ LSPosed 里 HookEuicc 已启用
→ 作用域里已经勾选 giffgaff
→ 勾选后已经重启模拟器

再安装 Via 浏览器。

建议把 Via 设置成默认浏览器，因为登录、付款、网页跳转时更稳。

最后安装 giffgaff App。

这一关的验收标准：

→ HookEuicc 已启用
→ HookEuicc 作用域已勾选 giffgaff
→ Via 已安装并设为默认浏览器
→ giffgaff App 已安装
→ 模拟器已重启

## Step 7：确认 giffgaff 识别 eSIM 能力

重启模拟器。

打开 giffgaff App。

进入 eSIM 页面。

如果前面都正确，原来“手机不支持 eSIM”的提示应该消失。

这一步是整套流程最重要的验收点。

![Article image](/assets/2026-09-08-0成本教你开-giffgaff-esim，保姆教程，有手就行-8aea7729cd/09.jpg)

如果 giffgaff 仍然提示不支持 eSIM，按这个顺序排查：

→ MuMu 是否开启 Root？
→ 磁盘是否选择可写系统磁盘？
→ Magisk 是否直接安装到系统？
→ LSPosed 是否作为 Magisk 模块安装？
→ LSPosed 管理器是否能打开？
→ HookEuicc 是否安装？
→ HookEuicc 模块开关是否打开？
→ HookEuicc 作用域是否勾选 giffgaff？
→ 勾选后是否重启模拟器？

这一关的验收标准：

→ giffgaff 不再提示设备不支持 eSIM
→ 可以进入 eSIM 购买 / 开通流程

## Step 8：购买 giffgaff eSIM

确认 giffgaff 识别 eSIM 后，就可以购买。

流程大概是：

→ 打开 giffgaff App
→ 登录账号
→ 切换到 eSIM
→ 选择充值 / 购买
→ 选择付款方式
→ 填写地址
→ 完成支付
→ 获取 eSIM 激活码

![Article image](/assets/2026-09-08-0成本教你开-giffgaff-esim，保姆教程，有手就行-8aea7729cd/10.jpg)

如果付款失败，不要马上回去重装 LSPosed。

到了付款环节，说明设备识别链路大概率已经通了。

付款失败更可能是这些原因：

→ 银行卡不支持
→ 地址不匹配
→ 网络环境异常
→ giffgaff 风控
→ 账号状态问题

这一关的验收标准：

→ 完成购买 / 充值
→ 拿到 giffgaff eSIM 激活码

## Step 9：处理 eSIM 激活码格式

完整 eSIM 激活码通常长这样：

→ LPA:1$服务器地址$激活码

但 giffgaff 给出的激活码，可能没有前面的 `LPA:`。

如果你把激活码导入某些 eSIM 工具或适配器时，它提示格式错误，可以尝试在前面补上：

→ LPA:

![Article image](/assets/2026-09-08-0成本教你开-giffgaff-esim，保姆教程，有手就行-8aea7729cd/11.jpg)

也就是把：

→ 1$服务器地址$激活码

改成：

→ LPA:1$服务器地址$激活码

注意：

只补前缀。

不要改服务器地址。

不要改激活码主体。

这一关的验收标准：

→ 激活码格式被 eSIM 工具识别
→ 不再提示格式错误

## Step 10：如果用 9esim 下发，先开全局英国节点

这是我自己踩过的坑。

我一开始用 9esim 下发 eSIM 文件，一直失败。

后来发现，不是文件问题，不是 eSIM 问题，而是网络环境没走对。

建议：

→ 下发前先开全局英国节点
→ 不要只开浏览器代理
→ 确保模拟器 / 下发工具也走英国网络

![Article image](/assets/2026-09-08-0成本教你开-giffgaff-esim，保姆教程，有手就行-8aea7729cd/12.jpg)

很多技术问题，看起来像工具坏了，实际只是网络没走对。

这一关的验收标准：

→ eSIM 可以正常下发 / 安装到目标方案

## 最后给一张总排查表

如果你卡住了，不要从最后一步乱试。

按依赖链往回排。

- Magisk 装不上：Step 2：Root + 可写系统盘
- Magisk 没权限：Root 授权是否点了永久允许
- LSPosed 找不到入口：Step 5：安装 manager.apk
- giffgaff 仍提示不支持 eSIM：Step 6：HookEuicc 是否启用并勾选 giffgaff
- 付款失败：支付方式、地址、账号风控、网络环境
- eSIM 下发失败：Step 10：是否全局英国节点
- 激活码格式错误：Step 9：是否缺少 `LPA:` 前缀

整套方法的本质就是这条链：

→ 模拟器能力
→ → Root
→ → Magisk
→ → LSPosed
→ → HookEuicc
→ → giffgaff 识别 eSIM
→ → 购买
→ → 激活码格式
→ → 网络下发

你在哪一步失败，就回到它上一层依赖。

别跳。

跳步骤，是这类教程最大的坑。

## 一句话总结

国行 iPhone 不能直接装 eSIM，但你可以先用电脑里的安卓模拟器把 giffgaff eSIM 开出来。

模拟器不是最终使用 eSIM 的地方。

模拟器只是开卡工具。

拿到激活码之后，后面才是安装、转接和下发问题。
