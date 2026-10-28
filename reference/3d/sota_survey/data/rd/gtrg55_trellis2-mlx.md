# trellis2-mlx

![macOS](https://img.shields.io/badge/macOS-Apple_Silicon-black)
![MLX](https://img.shields.io/badge/backend-MLX-blue)
![Python](https://img.shields.io/badge/Python-3.10-blue)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Native MLX backend for TRELLIS.2 on Apple Silicon, with practical 1024^3
image-to-3D generation and textured GLB export.**

Tested on a MacBook Pro with an M4 Max and 128 GB of unified memory.

[TRELLIS.2](https://github.com/microsoft/TRELLIS.2) is Microsoft's 4B-parameter
image-to-3D model. This project brings the generation pipeline to Apple Silicon
with MLX model execution, Metal-accelerated processing, and a Gradio interface
focused on usable high-resolution exports.

## Highlights

- **Stable 1024^3 generation** using chunked sparse texture sampling on MPS
- **512^3 dense MPS mode** for faster generation with lower memory requirements
- **Textured GLB export** with base color, metallic, roughness, and alpha data
- **Opaque material mode** by default, avoiding the transparent point-cloud-like
  appearance produced by unintended alpha blending
- **Fast Repair** for conservative mesh cleanup without joining distant surfaces
- **Optional Watertight Voxel Remesh** at 384 or 512 grid resolution
- **Topology diagnostics** for watertightness, boundary edges, and non-manifold edges
- **CPU dense fallback** for 1024^3 texture sampling

## Visual Comparison

<table>
  <tr>
    <th width="50%">Input image</th>
    <th width="50%">GLB rendered in Blender</th>
  </tr>
  <tr>
    <td><img src="assets/readme/dreaming-character-input.jpg" alt="Dreaming character input" width="100%"></td>
    <td><img src="assets/readme/dreaming-character-blender.gif" alt="Dreaming character GLB rendered in Blender" width="100%"></td>
  </tr>
  <tr>
    <td><img src="assets/readme/winged-statue-input.png" alt="Winged statue input" width="100%"></td>
    <td><img src="assets/readme/winged-statue-blender.gif" alt="Winged statue GLB rendered in Blender" width="100%"></td>
  </tr>
  <tr>
    <td><img src="assets/readme/astronaut-cat-input.png" alt="Astronaut cat input" width="100%"></td>
    <td><img src="assets/readme/astronaut-cat-blender.gif" alt="Astronaut cat GLB rendered in Blender" width="100%"></td>
  </tr>
</table>

## Requirements

- Apple Silicon Mac (M-series)
- macOS
- Conda or Miniconda
- Python 3.10
- About 15 GB of free disk space for the TRELLIS.2 model weights

The current release was tested with 128 GB of unified memory. Lower-memory
configurations may work, especially at 512^3, but have not been validated yet.

## Installation

```bash
git clone https://github.com/gtrg55/trellis2-mlx.git
cd trellis2-mlx

conda create -n trellis2-mlx python=3.10 -y
conda activate trellis2-mlx

python -m pip install --upgrade pip setuptools wheel
python -m pip install "torch>=2.11.0" "torchvision>=0.26.0"
python -m pip install --no-build-isolation -r requirements_macos.txt
python -m pip install --no-build-isolation ./o-voxel
```

Download the official TRELLIS.2 weights:

```bash
python scripts/download_weights.py
```

The weights are stored in `weights/TRELLIS.2-4B` and are excluded from Git.
The first launch may also download the image encoder and background-removal
models from Hugging Face.

## Run

```bash
conda activate trellis2-mlx
python app_mlx.py
```

Open the local Gradio URL printed in the terminal.

## Recommended Settings

For the best balance of speed and output quality:

| Setting | Recommended value |
| --- | --- |
| Resolution | `1024` |
| Texture Size | `1024` or `2048` |
| Texture Sampling | `GPU (Experimental Sparse Batching)` |
| Material Mode | `Opaque (Recommended)` |
| Mesh Repair | `Fast Repair` |
| Decimation Target | `200000` |

Resolution 512 always uses dense MPS texture sampling. At resolution 1024,
the UI provides experimental sparse MPS sampling and a slower dense CPU
fallback.

## Mesh Repair Modes

### Fast Repair

The default mode. It merges coincident vertices, removes duplicate geometry and
small disconnected fragments, fixes winding and normals, and closes simple
holes. It deliberately avoids proximity-based welding, which could create long
triangles between unrelated parts of a model.

### Watertight Voxel Remesh

Reconstructs the surface on a 384 or 512 voxel grid before UV unwrapping and
texture baking. It is useful when a closed surface matters more than preserving
every small geometric detail. It is slower and may smooth thin structures.

## Known Limitations

- `Fast Repair` does not guarantee a watertight or manifold mesh.
- Complex intersecting surfaces may retain visible seams or open boundaries.
- `Watertight Voxel Remesh` can smooth thin or highly detailed geometry.
- The TRELLIS.2 texture model can occasionally generate isolated color outliers.
- 1024^3 generation is compute-intensive and can take several minutes.
- Sparse MPS texture sampling is experimental.

The Gradio result panel reports boundary-edge and non-manifold-edge counts so
export quality can be checked before using the asset downstream.

## Testing

```bash
python -m unittest -v test_sparse_batched_sampling.py test_mesh_repair.py
```

The sparse sampler tests compare the MPS implementation against the original
`flex_gemm` interpolation behavior.

## Credits

- [Microsoft TRELLIS.2](https://github.com/microsoft/TRELLIS.2) and the
  [TRELLIS.2-4B model](https://huggingface.co/microsoft/TRELLIS.2-4B)
- [Pedro Naugusto](https://github.com/pedronaugusto) for the foundational
  Apple Silicon and MLX port

## License

This repository is released under the [MIT License](LICENSE). Model weights and
third-party dependencies may be subject to their own license terms.

Made with love for the Apple Silicon community.
