# riscv-check 工具改进计划

> 基于 BenBE (htop maintainer) 的反馈

---

## 🎯 改进目标

### 当前问题

根据 htop 维护者的反馈，riscv-check 工具存在以下问题：

1. **报告太长** - 生成 5+ 屏幕的报告
2. **格式混乱** - 混用中英文、大量 emoji
3. **推理不清晰** - 缺少 Coverity 风格的推理链条
4. **无根据声明** - "works on x86 but not on RISC-V" 没有证据
5. **AI 风格明显** - 看起来像 ChatGPT 生成的
6. **链接失效** - "htop example" 链接不可用

### 改进方向

1. **生成简洁报告** - < 2 屏幕
2. **专业格式** - 无 emoji，单语言
3. **清晰推理** - Coverity 风格
4. **提供证据** - 每个声明都有根据
5. **可测试性** - 提供验证方法
6. **人工审查** - 输出前需要人工确认

---

## 📋 改进项目清单

### Phase 1: 报告格式改进（优先级：高）

#### 1.1 添加报告模式选项

```python
# cli.py
@click.option('--report-style',
              type=click.Choice(['verbose', 'concise', 'minimal']),
              default='verbose',
              help='Report style: verbose (detailed), concise (standard), minimal (bug report only)')
```

**实现**：
```python
def generate_report(report_style):
    if report_style == 'verbose':
        # 旧格式（5+ 屏幕）- 用于学习
        return generate_verbose_report()
    elif report_style == 'concise':
        # 新格式（1-2 屏幕）- 默认推荐
        return generate_concise_report()
    elif report_style == 'minimal':
        # 最小格式（用于 Issue）
        return generate_minimal_report()
```

#### 1.2 实现简洁报告格式

```python
def generate_concise_report(issues):
    """Generate concise report (< 2 screens).

    Format:
    - Summary: 1 paragraph
    - Issues: bullet points with code snippets
    - Total: < 50 lines
    """
    report = []
    report.append(f"# RISC-V Compatibility Analysis\n")
    report.append(f"## Summary\n")
    report.append(f"Analyzed {project.files} files, found {len(issues)} issues.\n")

    for issue in issues[:10]:  # 最多显示 10 个
        report.append(f"### {issue.rule_id} at {issue.file}:{issue.line}\n")
        report.append(f"```c\n{issue.code_snippet}\n```\n")
        report.append(f"**Issue**: {issue.message}\n")
        report.append(f"**Fix**: {issue.suggestion}\n\n")

    return "".join(report)
```

#### 1.3 移除所有 emoji

```python
# report/model.py
def format_message(message):
    """Remove emojis and markdown decorations."""
    # 移除 emoji
    import emoji
    message = emoji.replace_emoji(message, '')

    # 移除多余的格式
    message = message.replace('**', '')
    message = message.replace('`', '')

    return message
```

#### 1.4 强制单语言

```python
# cli.py
@click.option('--language',
              type=click.Choice(['en', 'zh']),
              default='en',
              help='Report language (en or zh)')
```

```python
def generate_report(language):
    if language == 'en':
        template = EN_TEMPLATE
    else:
        template = ZH_TEMPLATE

    # 不混用
    return template.render(issues)
```

---

### Phase 2: 推理链条改进（优先级：高）

#### 2.1 实现 Coverity 风格推理

```python
# analyzers/base.py
class Issue:
    def get_coverity_style_report(self):
        """Generate Coverity-style reasoning chain.

        Format:
        1. Show code
        2. Explain requirements
        3. Show violation
        4. Explain impact
        """
        return f"""
## {self.rule_id}: {self.title}

### Code
```c
{self.code_snippet}
```

### Analysis
- **Type**: {self.source_type} (alignment: {self.source_alignment})
- **Cast to**: {self.target_type} (alignment: {self.target_alignment})
- **Requirement**: {self.target_alignment} > {self.source_alignment}
- **Violation**: Misaligned access

### Impact
On RISC-V: Triggers SIGBUS
On x86_64: Works (tolerates misalignment)

### Fix
{self.suggestion}

### Verification
{self.verification}
"""
```

#### 2.2 添加证据支持

```python
# report/model.py
class Issue:
    def __init__(self, ...):
        # 现有字段
        self.file = file
        self.line = line
        self.message = message

        # 新增字段
        self.evidence = []  # 支持证据
        self.test_case = None  # 可测试的例子

    def add_evidence(self, claim, proof):
        """Add evidence for a claim.

        Example:
            add_evidence(
                "RISC-V requires 8-byte alignment",
                "RISC-V ISA spec section 2.3: ..."
            )
        """
        self.evidence.append({"claim": claim, "proof": proof})
```

---

### Phase 3: 工具质量改进（优先级：中）

#### 3.1 添加人工审查确认

```python
# cli.py
@click.option('--auto-confirm',
              is_flag=True,
              help='Skip confirmation and submit directly (NOT RECOMMENDED)')
```

```python
def main():
    # ... 分析代码 ...

    # 生成报告
    report = generate_report(issues, style='concise')

    # 显示报告
    print(report)

    # 人工确认
    if not auto_confirm:
        click.echo("\n--- Report Preview ---")
        click.echo("Please review before submitting:")
        click.echo("1. Is it concise (< 2 screens)?")
        click.echo("2. Is reasoning clear?")
        click.echo("3. Are all claims supported by evidence?")
        click.echo("4. Are all links valid?")

        if not click.confirm("\nSubmit this report?"):
            click.echo("Aborted.")
            return

    # 提交或保存
    if output_file:
        save_report(report, output_file)
```

#### 3.2 链接验证

```python
# report/model.py
import requests

def validate_links(report):
    """Validate all links in report."""
    import re

    # 提取所有链接
    links = re.findall(r'https?://[^\s\)]+', report)

    valid = []
    for link in links:
        try:
            response = requests.head(link, timeout=5)
            if response.status_code == 200:
                valid.append(link)
            else:
                click.echo(f"Warning: Link {link} returned {response.status_code}", err=True)
        except Exception as e:
            click.echo(f"Warning: Could not verify {link}: {e}", err=True)

    return len(valid) == len(links)
```

#### 3.3 长度检查

```python
# report/model.py
def check_report_length(report, max_screens=2):
    """Check if report fits in max_screens.

    Assumes 1 screen = 40 lines
    """
    lines = report.count('\n')
    max_lines = max_screens * 40

    if lines > max_lines:
        click.echo(f"Warning: Report is {lines} lines (max {max_lines})", err=True)
        click.echo("Please shorten the report.", err=True)
        return False

    return True
```

---

### Phase 4: 输出质量控制（优先级：中）

#### 4.1 AI 检测特征移除

```python
# report/formatter.py
def remove_ai_patterns(text):
    """Remove patterns that make text look AI-generated."""

    # 移除过度结构化
    text = re.sub(r'#+ (🚀|💡|🔍|📖|🙏|❌|✅)', '', text)

    # 移除过度热情
    text = re.sub(r'(Revolutionary|Groundbreaking|Game-changing|Cutting-edge)', '', text, flags=re.IGNORECASE)

    # 移除重复强调
    text = re.sub(r'(Very|Really|Extremely)\s+(important|critical)', r'\1', text, flags=re.IGNORECASE)

    # 移除模糊术语
    text = re.sub(r'(Leverage|Utilize)\s+(AI|machine learning)', 'Use', text, flags=re.IGNORECASE)

    return text
```

#### 4.2 技术术语精确化

```python
# report/formatter.py
def make_technical(text):
    """Make text more technical and precise."""

    # 替换模糊术语
    replacements = {
        "a lot of": "multiple",
        "very fast": "efficient",
        "really good": "effective",
        "super important": "critical",
        "kind of": "approximately",
        "sort of": "partially",
    }

    for old, new in replacements.items():
        text = re.sub(old, new, text, flags=re.IGNORECASE)

    return text
```

---

### Phase 5: 用户体验改进（优先级：低）

#### 5.1 交互式报告编辑

```python
# cli.py
@click.option('--interactive', is_flag=True)
def interactive_report():
    """Interactive report editing before final output."""

    # 生成初稿
    draft = generate_report(issues)

    # 进入编辑器
    edited = click.edit(draft)

    if edited:
        # 使用编辑后的版本
        final = edited
    else:
        # 用户取消，使用初稿
        final = draft

    return final
```

#### 5.2 报告模板选择

```python
# cli.py
@click.option('--template',
              type=click.Path(exists=True),
              help='Use custom report template')
```

```python
def load_template(template_path):
    """Load custom Jinja2 template."""
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(template_path)

    return template
```

---

## 📊 实施优先级

### Week 1: 立即改进（必须）

1. ✅ 添加 `--report-style` 选项
2. ✅ 实现简洁报告格式
3. ✅ 移除所有 emoji
4. ✅ 强制单语言

**预期效果**：生成的报告符合基本标准

### Week 2-3: 质量提升（重要）

5. ✅ 实现 Coverity 风格推理
6. ✅ 添加证据支持
7. ✅ 人工审查确认
8. ✅ 链接验证

**预期效果**：报告质量接近 Coverity

### Week 4+: 体验优化（可选）

9. ⏳ 交互式编辑
10. ⏳ 自定义模板
11. ⏳ AI 检测特征移除

**预期效果**：更好的用户体验

---

## 🎯 成功标准

### 报告质量检查清单

生成报告后，自动检查：

- [ ] 长度 < 2 屏幕（80 行）
- [ ] 无 emoji
- [ ] 单语言（不混用）
- [ ] 第一段就说明问题
- [ ] 每个声明都有证据
- [ ] 推理链条清晰
- [ ] 所有链接有效
- [ ] 提供了测试方法
- [ ] 人工审查过

### 维护者满意度

**目标**：
- ✅ 报告被接受（不关闭）
- ✅ 维护者认真回复
- ✅ 建立长期关系

---

## 📝 示例对比

### 旧报告（被 BenBE 批评）

```markdown
🚀 RISC-V 迁移检测工具分析报告

## 📖 背景介绍

RISC-V 是一个开放的指令集架构，近年来...（3 屏废话）

## 💡 工具介绍

riscv-check 是一个革命性的工具...（营销话术）

## 🔍 htop 案例分析

我们选择 htop 作为第一个真实项目测试...（冗长）

## ❌ 发现的问题

在分析过程中，我们发现...（终于到重点了）

## 🙋‍♂️ 额外说明

FAQ 部分...

## 📚 参考资料

更多链接...

Total: 5+ screens, lots of emojis, mixed languages
```

### 新报告（符合标准）

```markdown
# Misaligned pointer access in XUtils.c:163

## Issue

Function xRealloc returns void* but is cast to char** at line 163
without verifying alignment, which may trigger SIGBUS on RISC-V.

## Code

```c
// XUtils.c:163
out = (char**)xRealloc(out, sizeof(char*) * blocks);
```

## Analysis

- Source: void* (unknown alignment to tool)
- Target: char** (8-byte alignment required)
- RISC-V requirement: Strict alignment
- Violation: Potential SIGBUS if misaligned

Note: xRealloc internally uses realloc() which returns aligned memory,
so this is a false positive. Tool has been updated to detect
__attribute__((malloc)) to avoid such issues.

## Impact

- x86_64: Works (tolerates misalignment)
- RISC-V: Would SIGBUS if truly misaligned
- Actual: Safe (xRealloc returns aligned memory)

## Status

False positive - tool improved based on analysis.

Total: 25 lines, no emojis, clear reasoning
```

---

## 🚀 下一步行动

### 立即执行

1. **创建新分支**：`feature/concise-reports`
2. **实现 Phase 1**：报告格式改进
3. **测试**：重新分析 htop，生成简洁报告
4. **对比**：新旧报告对比

### 本周目标

- [ ] 实现 `--report-style` 选项
- [ ] 移除所有 emoji
- [ ] 强制单语言输出
- [ ] 测试简洁报告格式

### 验证方法

重新分析 htop：
```bash
riscv-check htop --report-style concise --language en --output htop_concise.md
```

检查输出：
- [ ] < 2 屏幕？
- [ ] 无 emoji？
- [ ] 纯英文？
- [ ] 第一段说明问题？

---

**使用这个改进计划，riscv-check 将生成符合专业标准的报告！** 🎯
