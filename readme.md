# Building NEP automatically

This python package helps you build NEP with active learning technique. It use the same strategy with **MTP** [J. Chem. Phys. 159, 084112 (2023)] and **ACE** [Phys. Rev. Materials 7, 043801 (2023)].

It performs active learning by submitting and monitoring jobs automatically. It uses the following procedure:

### 1. Caculating energy, force and virial by *ab initio* calculations.

If it is the first iteration, and you don't have any structures, you can build some simple structures. For example, you can rattle the crystal structure to get an initial training set.

If you already have a `train.xyz` (with energy and force) before the first iteration, this step will be skipped.

Note that the inital training set cannot be too small for selecting the active set. If you use a NEP with a 30\*30 neural network, you need around 1000 local environments (10 structures with 100 atoms). If your NEP have *N* elements, then you need *N*\*1000 local environments for each element type.

### 2. Training and NEP.

Training an NEP with the structures in step-1. If you provide a `nep.txt`, this step will be skipped in the first iteration.

### 3. Selecting an active set.

Using `MaxVol` algorithem to select an active set. An active set is a set of reference environments to calcuting the extrapolation level.

### 4. Performing MD and get new structures. If there are no strucatures, the loop will be over.

Running GPUMD to atively selecting new structures based on extraplolation level cutoff. You can run multiple MD simulations at different conditions to explore faster.

### 5. Selecting structures to add to the training set.

The structures in step-4 have large extrapolation level, but there is no guarantee that they are diverse enough. So we perform another MaxVol selection to get the best structures.

# Installation

### 三级标题

#### 四级标题

##### 五级标题

###### 六级标题

---

## 文本格式

- **加粗文本**：`**加粗文本**`
- *斜体文本*：`*斜体文本*`
- ~~删除线~~：`~~删除线~~`
- `行内代码`：`` `行内代码` ``
- 高亮文本：`==高亮文本==`（部分 Markdown 解析器支持）

---

## 列表

### 无序列表

- 项目 1
- 项目 2
  - 子项目 2.1
  - 子项目 2.2
- 项目 3

### 有序列表

1. 第一项
2. 第二项
   1. 子项 2.1
   2. 子项 2.2
3. 第三项

---

## 链接和图片

- [普通链接](https://www.example.com)：`[普通链接](https://www.example.com)`
- [带标题的链接](https://www.example.com "标题")：`[带标题的链接](https://www.example.com "标题")`
- 图片：`![替代文本](https://www.example.com/image.png "图片标题")`

---

## 代码块

### 行内代码

这是一个 `print("Hello, World!")` 的示例。

### 代码块

```python
def hello_world():
    print("Hello, World!")