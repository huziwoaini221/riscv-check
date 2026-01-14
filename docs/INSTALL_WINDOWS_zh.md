# Windows 安装指南

## 平台支持

| 平台 | 支持状态 | 说明 |
|------|---------|------|
| Linux | ✅ 完全支持 | 主要开发平台 |
| macOS | ✅ 完全支持 | 经过测试验证 |
| Windows + WSL 2 | ✅ 推荐 | Windows 用户的最佳选择 |
| Windows 原生 | ⚠️ 实验性 | 配置复杂，不推荐 |

---

## Windows 用户

### 推荐：使用 WSL 2（⭐⭐⭐⭐⭐）

**WSL 2 提供完整的 Linux 环境，是 Windows 用户的最佳选择。**

#### 为什么选择 WSL 2？

- ✅ **完全兼容 Linux**：所有功能完美运行
- ✅ **安装简单**：一条命令即可完成
- ✅ **性能优秀**：接近原生速度
- ✅ **无缝集成**：从 `/mnt/c/` 访问 Windows 文件

#### 安装步骤

**1. 安装 WSL 2**

以管理员身份打开 PowerShell，运行：

```powershell
wsl --install
```

这将默认安装 WSL 2 和 Ubuntu。

**2. 重启电脑**

**3. 在 WSL 中安装 riscv-check**

```bash
# 更新软件包列表
sudo apt update

# 安装依赖
sudo apt install -y clang llvm libclang-dev
sudo apt install -y gcc-riscv64-linux-gnu g++-riscv64-linux-gnu
sudo apt install -y python3 python3-pip

# 安装 riscv-check
pip3 install riscv-check
```

**4. 使用 riscv-check**

```bash
# 分析 Windows C: 盘中的项目
riscv-check /mnt/c/path/to/your/project

# 示例
riscv-check /mnt/c/Users/YourName/code/my-project
```

**5. 访问 Windows 文件**

WSL 2 自动挂载 Windows 驱动器：
- `C:\` → `/mnt/c/`
- `D:\` → `/mnt/d/`
- 你的用户文件夹 → `/mnt/c/Users/YourName/`

---

### 备选方案：Windows 原生运行（⚠️ 不推荐）

**Windows 原生支持理论上可行，但需要复杂的配置。**

#### 限制

- ⚠️ **libclang 配置复杂**：必须手动配置路径
- ⚠️ **无交叉编译**：`riscv64-linux-gnu-gcc` 不可用
- ⚠️ **功能受限**：必须跳过编译验证
- ⚠️ **问题较多**：测试较少

#### 安装步骤（仅适合高级用户）

**1. 安装 LLVM**

从以下地址下载并安装 LLVM：https://llvm.org/builds/

- 选择 Windows 的"预编译二进制文件"
- 安装到默认位置（例如 `C:\Program Files\LLVM`）

**2. 安装 Python**

- 从 https://www.python.org/ 下载 Python 3.10+
- 安装时勾选"Add Python to PATH"

**3. 找到 libclang.dll**

定位你的 libclang.dll 路径（示例）：
```
C:\Program Files\LLVM\bin\libclang.dll
C:\LLVM\bin\libclang.dll
```

**4. 设置环境变量**

添加到系统环境变量：
```
LIBCLANG_PATH=C:\Program Files\LLVM\bin\libclang.dll
```

或在 PowerShell 中设置：
```powershell
$env:LIBCLANG_PATH = "C:\Program Files\LLVM\bin\libclang.dll"
```

**5. 安装 riscv-check**

```powershell
pip install riscv-check
```

**6. 使用 riscv-check（有限制）**

```powershell
# 必须跳过交叉编译验证
riscv-check C:\path\to\project --no-compile
```

#### 故障排除

**错误：`找不到 libclang.dll`**

解决方法：正确设置 `LIBCLANG_PATH` 环境变量。

**错误：`找不到文件`**

解决方法：使用 Windows 路径格式：`C:\path\to\project`

**错误：找不到交叉编译器**

解决方法：使用 `--no-compile` 标志跳过验证。

---

## 对比

| 特性 | WSL 2 | Windows 原生 |
|---------|-------|-------------|
| **安装难度** | ⭐ 简单 | ⭐⭐⭐⭐⭐ 复杂 |
| **功能完整性** | ✅ 完整 | ⚠️ 部分 |
| **性能** | ✅ 优秀 | ✅ 良好 |
| **维护成本** | ✅ 低 | ⚠️ 高 |
| **推荐程度** | ✅ **推荐** | ⚠️ 仅限高级用户 |

---

## 常见问题

**Q: 不使用 WSL 可以运行 riscv-check 吗？**

A: 可以，但需要复杂的手动配置。强烈推荐使用 WSL 2。

**Q: WSL 2 会减慢分析速度吗？**

A: 不会，WSL 2 有接近原生的性能。文件 I/O 非常快。

**Q: 可以分析 D: 盘的项目吗？**

A: 可以，通过 `/mnt/d/path/to/project` 访问。

**Q: 每个项目都要重新安装 WSL 吗？**

A: 不需要，安装一次即可用于所有项目。

---

## 快速开始（WSL 2）

```bash
# 一次性设置
wsl --install
# （重启电脑）

# 在 WSL 终端中
sudo apt update && sudo apt install -y clang llvm libclang-dev python3-pip
pip3 install riscv-check

# 分析一个 Windows 项目
riscv-check /mnt/c/Users/YourName/code/project
```

---

**需要帮助？** 在 [GitHub](https://github.com/huziwoaini221/riscv-check/issues) 提交问题
