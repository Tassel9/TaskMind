# TaskMind 进程执行边界

权限审批决定是否允许执行工具，SandboxSupervisor 决定进程如何启动。

## 当前行为

当前没有可用的原生 OS 隔离后端。请求 `none`、`read_only` 或
`workspace_write` 隔离模式时，Shell 和第三方 stdio MCP 会拒绝启动，
不会自动降级成宿主机执行。

只有显式配置 `filesystem: "host"` 才会直接启动可信进程。
该模式的启动记录显示 `backend: "host"`、`sandboxed: false`，
不能据此声称文件系统或网络受到 OS 隔离。

## 保留的控制

- 内置文件工具校验工作区路径，拒绝路径越界。
- 工具执行仍经过权限规则、人工审批、超时和输出限制。
- MCP 只继承运行必需的环境变量，配置引用的变量按需注入。
- Task、Memory、Artifact 等工具通过窄接口和领域校验控制操作。
- Windows 电脑操作使用独占租约、Run 会话、目标绑定、新鲜观察和执行后验证。

## 配置示例

下面的显式宿主机模式仅适用于已确认可信的 MCP Server：

```json
{
  "sandbox": {
    "filesystem": "host",
    "network": "unrestricted",
    "readable_roots": [],
    "writable_roots": [],
    "allowed_domains": []
  }
}
```

`host` 模式不能强制网络策略或域名白名单。原生隔离、资源限制和
域名代理需要新的执行后端实现，当前不具备这些能力。
