# 00_REVIEW: snowpeak review rounds (newest first)

Team retrospective across all rounds: `../docs/team_review/2026-10-28/01_snowpeak_retrospective.md`.

| Round | Topic | Status |
|---|---|---|
| `r21_s4_hd2/` | S4_hd2: smoother rebuilt bangs, side locks, bow, coat, mittens | **current**. Only idle, walk and run built. Open issues: the bow is small in the S view, fringe roots show ridges, thin sheets are noisy. |
| `r20_blender_base/` | from-scratch Blender base model (Claude and Gemini tracks) | stopped. Helmet hair, V-shaped jaw, tube coat; direction changed to refining S4_hd. |
| `r19_blender_sprites/` | r18 model B baked to sprites | dead end. The 6.5-head design doesn't fit 48x64. S4_hd kept. |
| `r18_blender_model/` | independent Blender models A/B | dead end (still needed fixes) |
| `r17_gemini_model/` | Gemini-authored SDF model | dead end ("hideous") |
| `r16_face_slim_bangs/` | slimmer face, S fringe dots, 3/4 jaw taper | approved, folded into S4_hd variants |
| `r15_face_bangs/`, `r15_model_gemini/` | face and bangs pass; Gemini critique of our model | folded in; advice only |
| `r14_retime/` | `*_r14` clip retimes | approved, not yet in a release |
| `r13_anime_pixel/` | hand-pixel busts, turnaround, poses (`art/hand/S4`) | **approved canon** |
| `r13_sprite_face/` | sprite face pass | superseded by r15 |
| `r12_hd_model/` | HD SDF model (S4_hd) | basis of the hero release |
| `r12_illustration/` | vector illustration | rejected ("the illustrations look terrible") |
| `r11_actions/` | 13-clip action set | approved, now `releases/S4_actions_v1` and then `S4_hd_actions_v1` |
| `r10_*` | concept art, outline study, S4 jump, semi-chibi candidates | superseded (r10 notes below) |

---


## r10 (2026-10-22)
| Folder | What | Open first |
|---|---|---|
| `r10_concept_art/` | **High-res concept art** of S4 for cut-scenes and dialogue. Same 3D model, rendered at about 4x the game sprite, with the new HD anime face (teal eyes, lashes, brows, blush). 11 expressions, 8 poses, an 8-direction turnaround, plus transparent sprite sheets with JSON for the engine. | `portraits_x2.png`, `fullbody_poses_x2.png` |
| `r10_S4_jump/` | **Your favourite, S4**: one tapered ponytail under the back bow, stylized hair (clump lines + one highlight ring), consistent face cels (eyes aligned, 3/4 faces mirrored), no scarf or hair clipping. Includes game sheet + JSON. | `jump_sc_8dir.gif`, `jump_sc_8dir_slow.gif` |
| `r10_semichibi_candidates/` | All 6 semi-chibi teal candidates after the hair stylists' pass. | `7_semichibi_candidates.gif` |
| `r10_outline_study/` | **Outline discussion**: the same sprite in 5 outline styles, plus the research doc, the art director's verdict and the game director's measurements. | `8_outline_styles_keys.png`, then the 3 `.md` files |

### Outline decision (team consensus)
* **Yes, keep a connected, closed outer outline.** At our size and camera distance, every open or lineless style "melts" into snow or rock (game director measured 5–59% of edge pixels below readable contrast).
* **Style: sel-out on a dark outline.** Lit edges use the material's own dark tone (softer, more ドット絵-like). The shadow side and feet stay near-black. A contrast floor switches back to near-black wherever a light material would vanish on snow.
* **Dark/night tiles:** the outer outline gets its own palette index, and the engine swaps it to a light rim on dark ground. The game director showed this brings melting to 0%.
* Reference games are in the research doc: FF Tactics (closest camera and size), Pokémon GBA/DS, Octopath, Sea of Stars, and others.
