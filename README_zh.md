# riscv-check

[English](README.md) | 简体中文

**检测 C/C++ 项目潜在 RISC-V 迁移问题的静态分析工具**

[![PyPI version](https://badge.fury.io/py/riscv-check.svg)](https://pypi.org/project/riscv-check/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## 概述

`riscv-check` 扫描 C/C++ 代码库，检测在严格对齐要求的架构上**可能**导致问题的模式：

- 潜在的内存对齐问题
- 架构特定的内联汇编
- 缺失 RISC-V 代码路径
- 未对齐的指针转换

## 为什么需要这个工具

### 问题所在

这段代码**可能**在 x86_64 上运行，但在严格对齐要求的架构上**可能导致未定义行为**：

```c
char *p = malloc(10);
p++;
int *i = (int*)p;  // 潜在未对齐地址
*i = 42;  // 可能导致对齐错误
```

**原因**：x86_64 在许多情况下容忍未对齐访问。RISC-V 要求 int 等类型严格对齐（通常 4 字节）。

### 解决方案

`riscv-check` 通过静态分析在迁移**之前**检测这些模式：

```bash
$ riscv-check /path/to/project

[ERROR] src/network.c:128 ALIGN_PTR_CAST
  在不验证对齐的情况下将 char* 转换为 int*
```

**注意**：这是静态分析工具。检测结果需要人工验证。

## 快速开始

### 安装

```bash
pip install riscv-check
```

### 基本使用

```bash
# 扫描项目
riscv-check /path/to/project

# 生成 maintainer 风格报告（一屏，无 emoji）
riscv-check /path/to/project --output report.md --report-style maintainer

# 跳过交叉编译验证
riscv-check /path/to/project --no-compile
```

### 报告模式

- `--report-style maintainer`（默认）：一屏专业格式
- `--report-style concise`：标准 < 2 屏幕报告
- `--report-style minimal`：仅 bug 报告，< 1 屏幕
- `--report-style verbose`：详细多页报告

### 语言控制

- `--language en`：仅英文（不混用）
- `--language zh`：仅中文

## 检测内容

### 1. 未对齐指针转换

**模式**：将指针转换为更严格的对齐要求

```c
// 在严格对齐架构上的潜在问题
char *p = get_buffer();
p++;  // 可能变得未对齐
int *i = (int*)p;  // 需要 4 字节对齐
*i = 42;  // 如果未对齐则未定义行为
```

**检测方法**：基于 AST 的静态分析，追踪指针来源和转换目标。

---

### 2. 紧凑结构体访问

**模式**：访问紧凑结构体的非 char 成员

```c
struct __attribute__((packed)) Packet {
    char type;
    int value;  // 未对齐字段
};

int x = packet->value;  // 可能导致对齐错误
```

**检测方法**：紧凑结构体字段访问模式。

---

### 3. 内联汇编

**模式**：架构特定的汇编代码

```c
// 不可移植
__asm__ volatile("movq %rax, %rbx");
```

**检测方法**：内联汇编块、架构特定指令。

---

### 4. 架构宏

**模式**：仅在特定架构上编译的代码

```c
#ifdef __x86_64__
    // 缺少 RISC-V 实现
#endif
```

**检测方法**：不平衡的架构特定代码路径。

## 风险评估

**风险分数**：0-100（启发式，非权威）

分数基于检测到的模式提供迁移就绪性的粗略指示。**不是**正确性保证。

| 分数 | 状态 | 建议 |
|-------|--------|----------------|
| 80-100 | 低风险 | 检测到较少模式 |
| 50-79 | 中风险 | 发现一些 ERROR 级模式 |
| 0-49 | 高风险 | 发现许多 ERROR 级模式 |

**评分方法（启发式）**：
- 基础分数：100
- 每个 ERROR：-20 分
- 每个 WARNING：-8 分
- 构建失败：-30 分

**重要提示**：这是启发式评分系统。实际迁移就绪性需要人工审查。

## 架构

```
输入：C/C++ 项目
  │
  ├─> 1. 项目扫描器
  │     - 解析 compile_commands.json
  │     - 收集源文件
  │
  ├─> 2. 静态分析 (libclang)
  │     - AST 遍历
  │     - 模式匹配
  │     - 类型检查
  │
  ├─> 3. 交叉编译验证（可选）
  │     - riscv64-linux-gnu-gcc
  │     - 构建错误提取
  │
  └─> 4. 报告生成
        - 控制台输出 (Rich)
        - Markdown 文件
        - Maintainer 格式（一屏）
```

## 环境要求

### 平台支持

| 平台 | 状态 | 备注 |
|----------|--------|-------|
| Linux | 支持 | 主要开发平台 |
| macOS | 支持 | 已测试验证 |
| Windows + WSL 2 | 支持 | Windows 用户推荐 |
| Windows 原生 | 实验性 | 配置复杂 |

### 系统要求

- Python 3.10+
- clang + libclang（用于 AST 解析）
- riscv64-linux-gnu-gcc（可选，用于交叉编译验证）

### 安装

**Ubuntu/Debian**：
```bash
sudo apt install clang llvm libclang-dev
sudo apt install gcc-riscv64-linux-gnu g++-riscv64-linux-gnu
```

**macOS**：
```bash
brew install llvm
brew install riscv-tools
```

## 文档

- [安装指南](docs/INSTALL.md)
- [Windows 安装](docs/INSTALL_WINDOWS.md)
- [使用指南](docs/USAGE.md)
- [架构设计](docs/ARCHITECTURE.md)
- [贡献指南](docs/CONTRIBUTING.md)

## 开发笔记

### 学习经历：误报案例研究 (2025-01)

**注意**：本节描述工具开发过程中的学习经历。

#### 背景

在早期开发阶段，此工具在一个中等规模、维护良好的 C 代码库上测试，以了解真实世界的 RISC-V 迁移模式。

#### 分析详情

- **代码量**：约 4 万行 C 代码
- **分析时间**：约 5 分钟
- **结果**：检测到 1 个对齐问题（后来证实为误报）

#### 工具改进历程

**初始发现**：
- 工具生成长篇报告，包含格式化装饰
- 标记一个自定义分配器函数为潜在问题
- 向项目维护者提交 issue

**维护者反馈**：
项目维护者提供专业反馈：
- **报告质量**：太冗长、过度格式化
- **技术准确性**：建议使用编译器属性而非硬编码函数列表
- **检测一致性**：注意到显式和隐式转换处理不一致

**改进措施**：
- 实现动态 `__attribute__((malloc))` 检测
- 添加隐式转换检测以保持一致性
- 完全重构报告格式：
  - Maintainer 风格一屏报告
  - 移除格式化装饰
  - 添加证据等级（E0/E1/E2）
  - 单语言强制

#### 经验教训

1. **误报**：标记的案例**不是**真正问题，因为分配器内部使用标准函数，根据 C 标准返回对齐的内存。

2. **工具成熟度**：早期版本对项目特定函数有硬编码假设。现在使用编译器标准属性以实现可移植性。

3. **报告质量**：维护者友好的报告需要：
   - 简洁
   - 最小化格式
   - 基于证据的推理
   - 专业技术写作

**注意**：提交的 issue 作为误报关闭。被分析的项目没有实际对齐问题。这次经历推动了工具的重大改进。

## 贡献

欢迎贡献。详见 [CONTRIBUTING.md](docs/CONTRIBUTING.md)。

```bash
# 开发环境设置
git clone https://github.com/huziwoaini221/riscv-check
cd riscv-check
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
black riscv_check/
mypy riscv_check/
```

## 路线图

### v0.1.0（当前 - MVP）
- [x] 未对齐指针转换检测
- [x] 紧凑结构体访问检测
- [x] 内联汇编检测
- [x] 架构特定宏
- [x] 交叉编译验证
- [x] Maintainer 风格报告
- [x] 证据等级分类

### v0.2.0（计划中）
- [ ] QEMU 动态验证
- [ ] CI/CD 管道集成
- [ ] 更多检测规则（原子操作、缓存一致性）

### v0.3.0（未来）
- [ ] Web UI 报告查看
- [ ] 团队协作功能

## 常见问题

**Q：检测准确率如何？**

A：工具旨在在 ERROR 级别发现上实现高精确度，但误报是预期的，特别是在早期版本。所有发现都需要人工验证。使用：
- 指针来源追踪
- `__attribute__((malloc))` 检测
- 交叉编译验证

**Q：能处理大型项目吗？**

A：已在 10,000+ 文件的项目上测试。随项目规模线性扩展。

**Q：会修改代码吗？**

A：不会。只读分析和报告。

**Q：如果没有 compile_commands.json 怎么办？**

A：工具可以工作，但精确度会降低。生成方法：
```bash
cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

## 致谢

我要感谢一个开源项目的贡献者，他们对对齐假设、分配器语义和报告质量标准提供了技术反馈。

他们的评论帮助识别了不正确的假设，并指导了此工具检测方法和报告格式的重大改进。

任何剩余的错误是我自己的。

### 依赖项目

- [clang](https://clang.llvm.org/) - C/C++ 解析和 AST 遍历
- [click](https://click.palletsprojects.com/) - CLI 框架
- [rich](https://rich.readthedocs.io/) - 终端输出格式化
- [RISC-V International](https://riscv.org/) - 架构规范

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 联系方式

- [报告问题](https://github.com/huziwoaini221/riscv-check/issues)
- [功能建议](https://github.com/huziwoaini221/riscv-check/discussions)
- 邮箱：thelazypig321@qq.com

---

**RISC-V 迁移静态分析**

如果这个工具有用，请考虑给项目加星！
