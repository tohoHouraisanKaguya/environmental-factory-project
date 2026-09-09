# AGENTS.md — environmental-factory-project 协作规范

> 适用范围：本仓库根目录及其全部子目录。  
> 目标：让人类成员与 Codex 在同一套规则下安全协作，保持 `main` 稳定、历史可追踪，并降低 Blender 二进制文件冲突风险。

---

## 1. 核心原则

1. **`main` 是唯一稳定主线和项目事实来源（source of truth）。**
2. **禁止直接在 `main` 上开发或直接推送功能性改动。**
3. 每个任务使用独立分支；一个分支只解决一个主题。
4. 所有非微小改动通过 Pull Request（PR）进入 `main`。
5. 合并前必须说明“改了什么、为什么改、如何验证”。
6. 不覆盖、删除或重写其他成员尚未合并的工作。
7. 不提交密码、Token、API Key、个人账号信息、私有证书或其他敏感信息。
8. Blender `.blend` 属于二进制文件：**默认不能依靠 Git 自动合并冲突**，必须采用单文件单写者规则。
9. 先保证可复现、可回滚，再追求“快”。
10. 每项任务完成后由 Codex 执行自审；验证通过且与最新 `main` 无冲突时，直接合并 PR，不再等待用户逐项确认。

---

## 2. 推荐工作流：轻量 GitHub Flow

每次开始新任务：

```bash
git switch main
git pull --ff-only origin main
git switch -c <type>/<short-description>
```

完成工作后：

```bash
git status
git diff
git add <明确的文件或目录>
git commit -m "<type>(<scope>): <summary>"
git push -u origin <branch-name>
```

随后在 GitHub 创建 Pull Request，完成自审并核对最新 `main`；检查通过且无冲突时直接合并。

### 禁止

```bash
git push origin main
git push --force
git reset --hard
git clean -fd
```

除非仓库负责人明确要求并确认风险。

> Codex 不得自行使用任何会丢失未提交修改、改写公共历史或强制覆盖远端的命令。

---

## 3. 分支命名

格式：

```text
<type>/<short-description>
```

推荐类型：

| 类型 | 用途 | 示例 |
|---|---|---|
| `feat/` | 新功能、新模型、新模块 | `feat/aeration-tank` |
| `fix/` | 修复错误 | `fix/pipe-routing` |
| `docs/` | 文档、报告说明 | `docs/design-notes` |
| `refactor/` | 重构但不改变目标功能 | `refactor/blender-generator` |
| `data/` | 数据、参数表整理 | `data/process-parameters` |
| `test/` | 测试、验证脚本 | `test/model-validation` |
| `chore/` | 仓库配置、依赖、杂项 | `chore/git-lfs` |

要求：

- 全部使用小写英文。
- 单词用 `-` 分隔。
- 名字应说明任务，不使用 `new`、`temp`、`test2`、`final` 等模糊名称。
- 一名成员默认只负责自己创建的任务分支；需要共同修改时先沟通。

---

## 4. Commit 规范

采用 Conventional Commits 风格：

```text
<type>(<scope>): <summary>
```

常用 `type`：

- `feat`：新增功能、模型或能力
- `fix`：修复错误
- `docs`：仅文档变化
- `refactor`：重构
- `test`：测试与验证
- `chore`：仓库配置、依赖、清理等

推荐 `scope`：

- `blender`
- `scripts`
- `data`
- `docs`
- `report`
- `repo`

示例：

```text
feat(blender): add aeration tank module
fix(scripts): correct pipe elevation calculation
docs(report): add process design assumptions
data(parameters): update influent design values
chore(repo): configure Git LFS for blend files
```

### Commit 要求

- 一个 commit 尽量只表达一个逻辑变化。
- 提交前必须检查 `git status` 和 `git diff`。
- 不使用以下模糊信息：

```text
update
fix
修改
final
final2
new version
111
```

- 不为了“提交方便”顺手加入无关文件。
- 已经存在于公共分支的 commit 不随意 amend/rewrite。
- Commit 描述可使用中文或英文，但同一 PR 内应保持一致；默认优先简洁英文。

---

## 5. Pull Request 规范

### 一个 PR = 一个明确任务

不要把以下内容混在一个 PR：

- 新建 Blender 模型
- 修改报告
- 清理整个仓库
- 顺手重构不相关脚本

如果任务可以独立审查，应拆分 PR。

### PR 标题

建议沿用 Commit 风格：

```text
feat(blender): add secondary sedimentation tank
```

### PR 描述必须包含

```markdown
## 目的
为什么需要这次修改？

## 主要改动
- ...
- ...

## 影响范围
涉及哪些目录、模型、数据或脚本？

## 验证
如何确认修改是正确的？
- [ ] 脚本可运行
- [ ] Blender 文件可正常打开
- [ ] 关键尺寸/参数已核对
- [ ] 未引入明显路径或资源缺失

## Blender / 可视化变化（如适用）
附截图、渲染图或说明。

## 大文件变化（如适用）
列出新增或修改的 `.blend` / 大型资源文件。

## 风险或待办
仍有哪些问题需要后续处理？
```

### Review 规则

- 文本文档、计算成果和脚本改动默认由 Codex 自审，不要求等待另一名成员或用户逐项批准。
- 自审必须基于最新 `main`，并检查 `git status`、任务范围内的 diff、可用测试或计算复核、数据来源与单位、敏感信息，以及 PR 是否可合并。
- 自审重点检查：
  - 是否满足任务目标
  - 是否影响其他模块
  - 是否误改无关文件
  - 参数/单位是否合理
  - Blender 资源是否缺失
  - 是否出现绝对路径、密钥或个人文件
- 上述检查通过且与最新 `main` 无冲突时，直接合并 PR，不等待额外确认。
- 遇到文本或二进制冲突、必需检查失败、敏感信息、不可逆操作，或足以使当前成果失效的高风险问题时停止自动合并并请求人工处理。
- 已明确记录、不会使本项结果失效且计划在后续项目闭合的工程假定，不单独阻塞合并。

### Merge 策略

小组项目默认推荐：

```text
Squash and merge
```

理由：一个任务最终在 `main` 中保留一个清晰提交，减少实验性 commit 对主线历史的干扰。

合并后删除已完成分支。

---

## 6. Blender 协作规则（重要）

### 6.1 `.blend` 文件必须按二进制资产处理

`.blend` 不应被当作普通文本文件尝试自动合并。

**同一个 `.blend` 文件同一时间只允许一名成员修改。**

在开始编辑共享 `.blend` 前：

1. `git pull` 获取最新主线；
2. 确认没有其他人正在修改同一文件；
3. 在小组任务/Issue/群聊中明确“该文件当前由谁负责”；
4. 完成后尽快提交 PR，不长期占用共享文件。

如果发现两个分支同时修改同一 `.blend`：

> 停止自动合并，先由成员人工确认保留方案。

不得让 Codex 直接选择 `ours` / `theirs` 来“解决” `.blend` 冲突。

---

### 6.2 主模型与模块模型分离

推荐结构：

```text
blender/
├── master/
│   └── factory_master.blend
├── units/
│   ├── pretreatment.blend
│   ├── aeration_tank.blend
│   ├── sedimentation_tank.blend
│   └── sludge_treatment.blend
└── assets/
```

规则：

- `factory_master.blend` 是集成文件，尽量只由指定集成人员修改。
- 普通成员优先在各自 `units/` 模块中工作。
- 模块完成后再由集成人员更新 master。
- 不用复制文件的方式做“版本管理”。

禁止：

```text
factory_final.blend
factory_final2.blend
factory_final_真的最终版.blend
```

Git 历史本身就是版本记录。

---

### 6.3 坐标、单位和路径

除非项目文档另有说明：

- 工程尺寸统一使用 **SI 单位**。
- Blender 默认按 **1 Blender Unit = 1 m** 处理。
- 使用 Blender 默认 Z-up。
- 不得随意移动项目约定的世界原点。
- 外部资源尽量使用**相对路径**，不得提交类似：

```text
C:\Users\张三\Desktop\...
D:\myfiles\...
```

- 新增外部纹理、模型、CSV 等资源时，必须确认其他成员 clone 后也能解析。

---

## 7. Git LFS 与大文件

所有需要编辑 `.blend` 文件的成员都应安装 Git LFS：

```bash
git lfs install
```

仓库应至少跟踪：

```bash
git lfs track "*.blend"
```

并提交生成的 `.gitattributes`：

```bash
git add .gitattributes
git commit -m "chore(repo): configure Git LFS"
```

### 重要

- `git lfs track` 不会自动把历史中已经提交的大文件迁移到 LFS。
- **不要由 Codex 擅自执行 `git lfs migrate` 或其他改写历史的操作。**
- 如需迁移已有历史，必须先由仓库负责人确认。
- 所有需要读取 LFS 文件的协作者都必须安装 Git LFS，否则 clone 后可能只拿到指针文件。

除 `.blend` 外，FBX、GLB、PSD、大型图片、视频和数据集是否使用 LFS，根据实际大小决定，不要无脑把所有文件都放进 LFS。

---

## 8. 数据与工程参数

工程项目中的“参数变化”与“代码变化”同样重要。

### 原始数据

- 原始测量/设计数据尽量保持只读。
- 不覆盖原始数据后只留下处理结果。
- 数据来源、单位和日期应可追溯。
- 重要参数修改需在 PR 中解释原因。

推荐：

```text
data/
├── raw/
├── processed/
└── parameters/
```

### 数据文件要求

- CSV 默认 UTF-8。
- 表头清楚表达含义和单位。
- 不把单位藏在个人记忆里。
- 不随意混用 `mm`、`m`、`L/s`、`m³/d` 等单位。
- 需要换算时优先由脚本显式完成并保留换算依据。

---

## 9. Python / Blender 自动化脚本

### 基本要求

- Python 使用 UTF-8。
- 缩进使用 4 个空格。
- 变量和函数命名应表达工程含义。
- 避免硬编码个人电脑绝对路径。
- 关键工程公式、参数来源和假设必须注释。
- 能拆成函数的逻辑不要全部堆在一个脚本顶层。
- 自动生成脚本在可行时应具有可重复运行性，不应每运行一次就无控制地重复生成对象。

### 依赖

如果新增第三方依赖：

1. 说明为什么需要；
2. 更新项目依赖说明；
3. 不要默认其他成员电脑已经安装；
4. Blender 自带模块与系统 Python 依赖要区分清楚。

---

## 10. 生成文件与临时文件

默认不提交：

- Blender 自动备份
- 缓存
- Python `__pycache__`
- IDE 配置
- 临时导出文件
- 中间渲染缓存
- 本地虚拟环境
- 操作系统垃圾文件

最终需要交付的图、表、模型、PDF 等可以提交，但必须明确其用途。

不要因为文件“看起来有用”就把整个 `output/`、缓存或本地环境全部加入 Git。

---

## 11. 安全规则

严禁提交：

```text
API_KEY
OPENAI_API_KEY
GitHub Token
密码
SSH 私钥
校园网账号密码
FRP Token
.env 中的真实秘密
个人身份证明文件
```

提交前若发现敏感信息：

1. 不要 push；
2. 从暂存区/工作区移除；
3. 通知仓库负责人；
4. 如果秘密已经推送，按泄露凭据处理并立即轮换，不能只“删掉文件”就认为安全。

---

## 12. Codex 专用操作规则

Codex 在执行任何仓库任务前必须：

1. 阅读本文件；
2. 查看：

```bash
git status
git branch --show-current
git log -5 --oneline
```

3. 了解相关目录和已有实现；
4. 确认不会覆盖当前未提交工作。

### Codex 默认行为

如果用户要求“完成任务并推送”，但没有指定 Git 流程：

1. 从最新 `main` 创建任务分支；
2. 只修改完成任务所需的文件；
3. 运行可用的检查/测试；
4. 检查 diff；
5. 按本文件规范 commit；
6. push 任务分支；
7. 如环境支持，创建 PR；
8. 获取最新 `main`，完成自审和冲突检查；无冲突且检查通过时直接合并 PR；
9. 向用户报告：
   - 分支名
   - commit
   - 主要修改
   - 验证结果
   - PR 地址和合并提交（若已创建并合并）

### Codex 禁止自行执行

- 直接 push `main`
- `git push --force`
- `git reset --hard`
- `git clean -fd`
- 删除他人分支
- 改写公共 commit 历史
- 擅自迁移 Git LFS 历史
- 擅自解决 `.blend` 二进制冲突
- 删除不属于当前任务的文件
- 提交凭据或私密信息

如果完成任务需要上述操作，先停止并向用户说明原因和风险。

---

## 13. 开工前 Checklist

```text
[ ] 当前 main 已更新
[ ] 已创建独立任务分支
[ ] 已确认任务边界
[ ] 若修改 .blend，已确认没有其他成员同时编辑
[ ] 工程单位/坐标约定明确
[ ] 没有秘密或个人路径进入仓库
```

---

## 14. 提交 PR 前 Checklist

```text
[ ] git status 已检查
[ ] git diff 已检查
[ ] 没有误提交临时文件
[ ] 没有绝对路径
[ ] 没有密码/Token/私钥
[ ] Blender 文件能打开
[ ] 相关脚本已运行或说明无法运行的原因
[ ] 参数、单位和数据来源已核对
[ ] PR 描述说明目的、改动和验证方法
[ ] 大型二进制文件变化已明确说明
```

---

## 15. Definition of Done

一个任务只有同时满足以下条件才算“完成”：

1. 任务目标已经实现；
2. 修改范围清晰；
3. 基本验证通过；
4. 没有已知的高风险未说明问题；
5. 文档/参数说明同步更新；
6. commit 和 PR 信息可理解；
7. 没有误提交临时文件或敏感信息；
8. 已 push 到远端任务分支；
9. 完成自审并确认与最新 `main` 无冲突后合并到 `main`；
10. 合并后删除废弃任务分支。

---

## 16. 冲突处理原则

### 文本文件

可以人工处理 merge conflict，但必须理解双方修改。

### `.blend` / 大型二进制文件

不要尝试文本式合并。

处理顺序：

1. 确认两边各自做了什么；
2. 决定一个版本作为基础；
3. 在 Blender 内人工重做另一边需要保留的修改；
4. 重新保存；
5. 验证后提交新的整合版本。

目标不是“让 Git 不再报错”，而是**保证工程内容正确**。

---

## 17. 规范优先级

出现冲突时按以下顺序执行：

1. 用户/仓库负责人的明确最新指令
2. 本 `AGENTS.md`
3. 目录内更具体的 `AGENTS.md`（若未来存在）
4. `README.md` / 设计说明
5. 工具默认行为

任何不确定、不可逆或可能覆盖他人工作的操作，都应先询问。

---

## 18. 本规范依据

本仓库采用的是适合小型工程团队的轻量规则，主要参考：

- GitHub Docs — Pull Requests / GitHub Flow  
  https://docs.github.com/en/pull-requests/get-started/about-pull-requests
- GitHub Docs — Branches / Protected Branches  
  https://docs.github.com/en/pull-requests/reference/branches
- GitHub Docs — Standardizing Pull Requests  
  https://docs.github.com/en/pull-requests/reference/managing-and-standardizing-pull-requests
- GitHub Docs — Git Large File Storage  
  https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage
- Conventional Commits 1.0.0  
  https://www.conventionalcommits.org/en/v1.0.0/
- OpenAI Codex — `AGENTS.md` instructions  
  https://openai.com/index/introducing-codex/

---

**原则总结：小分支、小提交、小 PR；`main` 保持稳定；Blender 二进制文件避免并行编辑；所有重要改动可追踪、可解释、可回滚。**

---

## 19. CAD / BIM 等同类建模程序

本规范中的 Blender 规则同样适用于 CAD、BIM 和其他会生成复杂工程模型的程序。除 `.blend` 外，以下类型也按不可自动合并的工程资产处理：`.dwg`、`.dxf`、`.rvt`、`.rfa`、`.ifc`、`.skp` 以及项目实际使用软件的专有工程格式。

统一要求如下：

- 同一个模型文件同一时间只由一名成员写入；开始编辑前先在 Issue、任务或群聊中登记负责人。
- 主模型、中心模型和模块模型分离；普通成员优先修改自己的模块文件，由指定集成人员更新主模型。
- 外部参照、链接模型、族、材质、纹理、字体和模板必须使用仓库内可访问的相对路径，并在 PR 中说明依赖。
- 使用项目约定的单位、坐标系、标高、图层/类别和命名规则；不得为了个人软件设置随意改变公共基准。
- PR 中附上模型版本、软件名称和版本、关键视图或导出结果，并说明是否发生链接、族或外部资源变化。
- 发生冲突时不得直接选择 `ours` / `theirs`；应在对应建模程序内人工整合，并由模型负责人验证尺寸、构件关系和外部链接。
- CAD/BIM 文件是否使用 Git LFS，按文件大小和团队软件流程决定；若需要迁移历史，必须先经仓库负责人确认。

因此，“Blender 文件单写者”应理解为“所有复杂建模工程文件单写者”，而不是只限制 `.blend` 文件。
