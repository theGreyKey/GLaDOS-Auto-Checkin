# GLaDOS 自动签到

基于 GitHub Actions，每天 UTC 04:00（北京时间 12:00）自动签到，支持多账号。

## 使用

1. Fork 仓库，启用 Actions。
2. 在 Settings → Secrets and variables → Actions 添加 `COOKIES`。
3. 填入浏览器已登录状态下的完整 Cookie 请求头，可手动运行工作流验证。

```text
字段名=字段值; 其他字段名=其他字段值
```

示例：
```
gld:sess=xxxxxx; gld:sess.sig=yyyyyy
```

不限制 Cookie 字段名，也不要求固定的签名字段。官方更名后只需更新 `COOKIES` 中的键值对，无需修改程序。多账号用 `|||`、换行或 `&` 分隔，推荐 `|||`。


## 可选功能

推送变量：`SENDKEY`、`SERVERCHAN_KEY`、`TG_BOT_TOKEN` + `TG_CHAT_ID`、`PUSHPLUS_TOKEN`、`DINGTALK_WEBHOOK`（可配 `DINGTALK_SECRET`）、`FEISHU_WEBHOOK`（可配 `FEISHU_SECRET`）、`WECOM_BOT_WEBHOOK`、`YUNHU_TOKEN` + `YUNHU_RECV_ID`（可配 `YUNHU_RECV_TYPE`）。

积分兑换：设置 `EXCHANGE_PLAN` 或 `GLADOS_EXCHANGE_PLAN` 为 `plan100` / `plan200` / `plan500`，分别消耗 100 / 200 / 500 积分兑换 10 / 30 / 100 天，默认关闭。

若签到返回“没有权限”，请重新登录并更新完整 Cookie。
