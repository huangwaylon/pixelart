
<h1 align="center">Strips as Tokens: Artist Mesh Generation<br>with Native UV Segmentation</h1>

<p align="center"><b>ACM Transactions on Graphics. SIGGRAPH 2026.</b></p>

<p align="center">
  <a href="https://ruixu.me/">Rui Xu</a><sup>1,2</sup>&nbsp;
  <a href="https://dafei-qin.github.io/">Dafei Qin</a><sup>1,2</sup>&nbsp;
  <a href="https://dolphinqiao.github.io/">Kaichun Qiao</a><sup>3,2</sup>&nbsp;
  <a href="https://qiujiedong.github.io/">Qiujie Dong</a><sup>4</sup>&nbsp;
  <a href="https://phj128.github.io/">Huaijin Pi</a><sup>1</sup>&nbsp;
  <a href="https://scholar.google.com/citations?user=YvwsqvYAAAAJ&hl=zh-CN">Qixuan Zhang</a><sup>3,2</sup>&nbsp;
  <a href="https://zhanglongwen.com/">Longwen Zhang</a><sup>3,2</sup><br>
  <a href="http://xu-lan.com/">Lan Xu</a><sup>3</sup>&nbsp;
  <a href="https://www.yu-jingyi.com/">Jingyi Yu</a><sup>3</sup>&nbsp;
  <a href="https://engineering.tamu.edu/cse/profiles/Wang-Wenping.html">Wenping Wang</a><sup>5</sup>&nbsp;
  <a href="https://www.cs.hku.hk/index.php/people/academic-staff/taku">Taku Komura</a><sup>1</sup>
</p>

<p align="center">
  <sup>1</sup>The University of Hong Kong&nbsp;&nbsp;
  <sup>2</sup>Deemos Technology&nbsp;&nbsp;
  <sup>3</sup>ShanghaiTech University&nbsp;&nbsp;
  <sup>4</sup>Shandong University&nbsp;&nbsp;
  <sup>5</sup>Texas A&M University<br>
</p>

<p align="center">
  <a href="http://arxiv.org/abs/2604.09132">
    <img src="https://img.shields.io/badge/Paper-PDF-red?logo=adobeacrobatreader" alt="Paper">
  </a>&nbsp;
  <a href="https://ruixu.me/html/SATO/index.html">
    <img src="https://img.shields.io/badge/Project-Page-blue?logo=googlechrome" alt="Project Page">
  </a>&nbsp;
</p>

<p align="center">
  <img src="assets/15ps.jpg" width="100%" alt="SATO teaser">
</p>

**Strips as Tokens (SATO)** enables unified, high-quality artist mesh generation with native UV segmentation. Our strip-based tokenizer supports both triangle and quad meshes without retraining and automatically segments UV charts during autoregressive generation.

> 🚀 The SATO tokenizer is now available in [`sato_tokenizer.py`](sato_tokenizer.py).

## 📋 Release Todo List

- [x] Release tokenizer code
- [ ] Release inference code

---

## Tokenizer

SATO serializes a mesh as long, connected face strips. A triangle strip appends
one vertex for each new face, while a quad strip appends two. Coordinates use the
same three-level hierarchical quantization and prefix sharing pattern as BPT and
DeepMesh, with paper-specific top-level tokens for strip and UV transitions.

The release is intentionally small: the complete implementation is one NumPy-only
file, with procedural `serialize`/`deserialize` functions in the style of the BPT
and DeepMesh tokenizers.

### Installation

```bash
pip install numpy
```

### Input contract

The tokenizer accepts any mesh-like object with two attributes:

- `vertices`: floating-point array with shape `(V, 3)`, normalized to `[-1, 1]`;
- `faces`: integer array with shape `(F, 3)` for triangles or `(F, 4)` for quads.

`serialize_quad` also accepts mixed triangle/quad arrays with shape `(F, 4)`.
Represent a triangle row as `[a, b, c, -1]`; native quad rows retain all four
indices. This padding exists only at the array interface and is never treated as
a mesh vertex.

SATO does not load or normalize meshes internally. This matches the preprocessing
pattern used by BPT and DeepMesh and keeps data transformations explicit.

For quad meshes, pass the original four-sided faces directly. Do not construct a
`trimesh.Trimesh` first: trimesh triangulates polygon faces. The included test OBJ
loader shows a minimal way to preserve `f` rows with three or four indices and
pad only the triangle rows when a file contains both.

### Triangle usage

```python
from sato_tokenizer import deserialize, serialize

# mesh.vertices: (V, 3), mesh.faces: (F, 3)
tokens = serialize(mesh, max_strip_faces=20)
vertices, faces, uv_labels = deserialize(tokens)
```

`tokens` is a one-dimensional `numpy.int64` array. The decoder returns quantized
vertex coordinates, triangle indices with shape `(F, 3)`, and one connected-
component/UV-island label per face.

### Quad usage

```python
from sato_tokenizer import deserialize_quad, serialize_quad

# quad_mesh.vertices: (V, 3), quad_mesh.faces: (F, 4)
tokens = serialize_quad(quad_mesh, max_strip_faces=20)
vertices, faces, uv_labels = deserialize_quad(tokens)
```

Quad faces are read directly and remain four-sided. Following Algorithm 1 in the
paper, the final two vertices are swapped in the serialized stream; the quad
detokenizer reverses that swap when constructing each face.

For a mixed mesh, native quads still use quad strips without triangulation. Each
residual triangle uses a three-vertex strip so its face is not dropped. Since the
quad decoder always returns an `(F, 4)` integer array, it represents that triangle
as the degenerate row `[a, b, c, c]`.

The geometry stream is topology-independent at decode time. For example, a valid
triangle token sequence can also be passed to `deserialize_quad` to pair adjacent
triangles, and a quad token sequence can be passed to `deserialize` for triangle
interpretation.

### Strip length limit

Both serializers use `max_strip_faces=20` as a configurable default, so each
extracted strip contains at most 20 faces unless the caller chooses otherwise.
Pass any positive integer to use a larger or smaller cap, or pass `None` for
unlimited strip growth. The SATO representation itself does not impose a 20-face
limit.

Choose the setting that fits your use case:

```python
tokens = serialize(mesh, max_strip_faces=64)
quad_tokens = serialize_quad(quad_mesh, max_strip_faces=None)
```

With `None`, a strip grows greedily until it reaches a topology boundary or an
already visited face. Changing this option changes the strip-length and
transition-token distribution, so use the desired setting consistently across
your data pipeline.

### Native UV segmentation

SATO treats edge-connected face components as UV islands. Before serialization,
vertices must be split along UV seams, as is standard when expanding OBJ-style
position/texture index pairs. After seam splitting, faces inside an island remain
edge-connected while faces across a UV boundary do not share vertex indices.

Within one component, new strips begin with `C1_t`. The first strip of the next
component begins with `C1_uv`, which simultaneously marks a strip transition and
a UV-island transition. These are coordinate-bearing top-level tokens, not extra
standalone separators.

### Vocabulary

Coordinates are quantized to a `512 x 512 x 512` grid using hierarchy sizes
`4 x 8 x 16`. The geometry vocabulary contains 4800 tokens:

| Token range | Meaning |
| --- | --- |
| `0-63` | standard top-level coordinate, `C1_geo` |
| `64-575` | second-level coordinate, `C2` |
| `576-4671` | third-level coordinate, `C3` |
| `4672-4735` | top-level coordinate beginning a new strip, `C1_t` |
| `4736-4799` | top-level coordinate beginning a new UV island, `C1_uv` |

Consecutive vertices share cached `C1`/`C2` prefixes. A `C1_t` or `C1_uv` token
resets that cache and is always followed by its explicit `C2` and `C3` values.
Model-level BOS, EOS, and padding IDs are intentionally outside this tokenizer.

Quantization is intentionally lossy. Vertices closer than one cell can decode to
the same index within a component, so extremely short source edges may collapse.
The token vocabulary does not carry separate original face-degree metadata.

### Tests and demos

`tests/data/` contains exactly four OBJ inputs. Their matching decoded,
component-colored PLY files are kept under `tests/output/`:

| OBJ input | Serialization | Source faces | Components | Decoded output |
| --- | --- | ---: | ---: | --- |
| `triangle_demo_01.obj` | triangle | 7,514 triangles | 25 | `triangle_demo_01_decoded_colored.ply` |
| `triangle_demo_02.obj` | triangle | 2,072 triangles | 16 | `triangle_demo_02_decoded_colored.ply` |
| `quad_bicycle.obj` | mixed quad | 4,450 quads + 303 triangles | 50 | `quad_bicycle_decoded_colored.ply` |
| `quad_exercise_machine.obj` | mixed quad | 3,165 quads + 621 triangles | 57 | `quad_exercise_machine_decoded_colored.ply` |

The quad demos provide 50 and 57 edge-connected parts, respectively, so the
component-colored result is visible at a glance. Their OBJ polygon rows are read
directly and never passed through a triangulating mesh container.

Run every unit and real-asset round-trip test with:

```bash
python test_tokenizer.py
```

The script verifies polygon-preserving OBJ loading, triangle and quad round trips,
the 4800-token layout, connected-component UV transitions, the optional 20-face
strip limit, mixed triangle/quad input, and all four demos. Each decoded sample is
rewritten to `tests/output/` as an ASCII PLY. Faces and vertices use a deterministic
RGB color per decoded connected-component/UV label, making separate components
directly visible in a PLY viewer.



---

## Abstract

Recent advancements in autoregressive transformers have demonstrated remarkable potential for generating artist-quality meshes. However, the token ordering strategies employed by existing methods typically fail to meet professional artist standards, where coordinate-based sorting yields inefficiently long sequences, and patch-based heuristics disrupt the continuous edge flow and structural regularity essential for high-quality modeling. To address these limitations, we propose **Strips as Tokens (SATO)**, a novel framework with a token ordering strategy inspired by triangle strips. By constructing the sequence as a connected chain of faces that explicitly encodes UV boundaries, our method naturally preserves the organized edge flow and semantic layout characteristic of artist-created meshes. A key advantage of this formulation is its unified representation, enabling the same token sequence to be decoded into either a triangle or quadrilateral mesh. This flexibility facilitates joint training on both data types: large-scale triangle data provides fundamental structural priors, while high-quality quad data enhances the geometric regularity of the outputs. Extensive experiments demonstrate that SATO consistently outperforms prior methods in terms of geometric quality, structural coherence, and UV segmentation.


## Ack
Our code is based on these wonderful works:
* **[DeepMesh](https://github.com/zhaorw02/DeepMesh)**
* **[MeshMosaic](https://github.com/Xrvitd/MeshMosaic)**
* **[BPT](https://github.com/Tencent-Hunyuan/bpt)**
* **[Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/tree/main/hy3dshape)**
