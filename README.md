# 📊 DeepSLO

[![GitHub commit activity](https://img.shields.io/github/commit-activity/t/CallStorm/DeepSLO)](https://github.com/CallStorm/DeepSLO/commits/main)
[![GitHub Stars](https://img.shields.io/github/stars/CallStorm)](https://github.com/CallStorm)
[![License](https://img.shields.io/github/license/CallStorm/DeepSLO?cacheSeconds=1)](LICENSE)

---

**DeepSLO** 是一套端到端的服务级别目标（Service Level Objectives, SLO）治理平台，面向 API / 数字体验团队构建。它集成 MeterSphere 拨测数据、自动计算月度与年度 SLO、实时追踪误差预算，并通过可配置的 AI 模型输出结构化洞察与诊断建议。

DeepSLO 让团队能够快速回答：

> 💡 “这个季度的误差预算还剩多少？”  
> “哪些拨测场景导致了连续中断？”  
> “针对本周异常，AI 建议的优化重点是什么？”

---

## ✨ Features

### 📈 数据驱动的 SLO 大屏
- 针对月度与年度周期实时呈现达成率、误差预算、拨测趋势
- 支持多项目切换、指标看板自定义时间范围

### 🔋 误差预算与中断分析
- 自动解析拨测失败窗口，按 cron 周期识别连续中断
- 计算总中断时长、有效拨测次数与趋势对比

### 🤖 AI 辅助洞察
- 通过 DeepSeek / 火山引擎 / OpenAI 兼容接口流式生成分析报告
- 在前端内置聊天体验，可导出 PDF 便于汇报与归档

### 🔁 MeterSphere 数据同步
- 基于 AccessKey/SecretKey 的安全认证
- 支持多项目同步、断点续传与失败重试
- 独立后台线程定时拉取拨测报告，自动入库

### 🛡️ 团队与系统管理
- JWT 鉴权 + RBAC 用户及项目管理
- AI 模型、同步配置、拨测规则均可在系统配置中维护

---

## 🚀 Installation

> ⚠️ **本地开发：**  
> - MySQL 8+ 并创建 `deepslo` 数据库 ，可以看下`db.py`里的配置；
> - Python 3.11+  
> - Node.js 18+ / npm 9+

1. 克隆仓库并初始化环境
   ```bash
   git clone https://github.com/CallStorm/DeepSLO.git
   cd DeepSLO
   ```

2. 配置后端
   ```bash
   cd DeepSLO
   pip install -r requirements.txt
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. 启动前端
   ```bash
   cd frontend
   npm install
   npm run dev  # 默认运行在 http://localhost:5173
   ```

4. 浏览器访问前端地址，使用默认账户 `admin / admin` 登录（请立即修改密码）。

---

## 🐳 Docker Support

- Docker Compose 样例正在完善中，欢迎提交 PR 或查看 `deploy/` 目录（更新中）。

---

## 🔧 Local Development

```bash
# 后端单元测试（示例）
cd backend
pytest

# 前端代码质量检查
cd ../frontend
npm run build
```

- 开发阶段建议开启 uvicorn `--reload`，前端使用 Vite HMR 获取实时反馈。
- 若需要调试 AI 流式输出，可在浏览器控制台观察 `/slo/analysis/chat` SSE。

---

## 🧭 Roadmap Highlights

- ✅ MeterSphere 拨测报告增量同步
- ✅ 月度 / 年度 SLO 自动计算
- ✅ AI 驱动的 SLO 智能分析与报告导出
- 🚧 自定义阈值预警与通知通道
- 🚧 Docker 一键部署脚本
- 📝 Grafana / Prometheus 指标输出

---

## 🤝 Contributing

欢迎贡献新功能与修复！

```bash
# Fork 后克隆
git checkout -b feature/your-feature

# 提交变更
git commit -m "feat: add your feature"
git push origin feature/your-feature
```

随后在 GitHub 上创建 Pull Request 并说明背景与测试情况。

---

## 🆘 Support & Community

- Issues: [GitHub Issues](https://github.com/CallStorm/DeepSLO/issues)
- 邮箱：support@callstorm.io
- 社区与更多文档：建设中，欢迎在 Issue 中反馈诉求

---

## 📄 License

本项目基于 MIT License 发布，详情参见 [LICENSE](LICENSE)。

---

## 🙏 Support Development

项目仍在早期迭代阶段，如需商务合作或定制支持，请联系 `510908220@qq.com`。