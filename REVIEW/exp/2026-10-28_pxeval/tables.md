## seq back-test

| group | clip | n | changed | resid | flicker | boil | shade_swap | motion_px | articulation | artic/s | rigid_share | pose_range | feet_rng | height_rng | seam_ratio | flags | critic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sw pilot anim96 | idle_SE gif | 4 | 0.466 | 0.007 | 0.264 | 0.005 | 0.002 | 0.859 | 0.030 | 0.101 | 0.939 | 0.229 | 0.000 | 1.000 | 0.727 | STIFF | motion 5 (Opus/Argon r2), "virtually zero motion", no_boiling 4 |
| sw pilot anim96 | idle_SE 1x | 6 | 0.311 | 0.005 | 0.100 | 0.001 | 0.002 | 0.572 | 0.020 | 0.101 | 0.939 | 0.229 | 0.000 | 1.000 | 0.727 | STIFF | same, 6 frames incl. 2 exact holds |
| sw pilot anim96 | walk_SE gif | 6 | 0.666 | 0.222 | 0.266 | 0.031 | 0.030 | 1.115 | 0.190 | 1.783 | 0.630 | 0.482 | 0.000 | 2.000 | 0.983 | BOILING SHADE_SWAP | motion 3 (Opus), legs never swap, face/hair boil, no_boiling 4 |
| sw pilot anim96 | walk_SE 1x | 6 | 0.666 | 0.222 | 0.266 | 0.031 | 0.030 | 1.115 | 0.190 | 1.783 | 0.630 | 0.482 | 0.000 | 2.000 | 0.983 | BOILING SHADE_SWAP | same |
| sw mocap 64px | dash_SE | 5 | 0.815 | 0.406 | 0.575 | 0.178 | 0.015 | 1.430 | 0.407 | 4.844 | 0.295 | 0.750 | 7.000 | 17.000 | 0.980 | BOILING FEET_JITTER | pose tables kept |
| sw mocap 64px | hurt_SE | 4 | 0.766 | 0.347 | 0.514 | 0.142 | 0.014 | 1.423 | 0.386 | 3.029 | 0.327 | 0.601 | 3.000 | 7.000 | 0.950 | BOILING FEET_JITTER | pose tables kept |
| sw mocap 64px | idle_SE | 6 | 0.350 | 0.100 | 0.221 | 0.020 | 0.007 | 0.514 | 0.196 | 0.981 | 0.316 | 0.313 | 0.000 | 3.000 | 0.848 | BOILING | pose tables kept |
| sw mocap 64px | jump_SE | 8 | 0.841 | 0.499 | 0.488 | 0.155 | 0.018 | 1.186 | 0.357 | 3.438 | 0.260 | 0.892 | 19.000 | 12.000 | 0.604 | BOILING SHADE_SWAP FEET_JITTER | pose tables kept |
| sw mocap 64px | overhead_SE | 6 | 0.682 | 0.310 | 0.361 | 0.127 | 0.010 | 1.174 | 0.312 | 2.638 | 0.360 | 0.698 | 0.000 | 10.000 | 0.902 | BOILING | pose tables kept |
| sw mocap 64px | run_SE | 6 | 0.620 | 0.222 | 0.389 | 0.068 | 0.006 | 1.135 | 0.386 | 5.262 | 0.248 | 0.559 | 5.000 | 6.000 | 1.124 | BOILING FEET_JITTER | pose tables kept |
| sw mocap 64px | slash_SE | 7 | 0.680 | 0.333 | 0.315 | 0.118 | 0.014 | 1.014 | 0.314 | 3.050 | 0.294 | 0.696 | 4.000 | 5.000 | 0.622 | BOILING FEET_JITTER | pose tables kept |
| sw mocap 64px | walk_SE | 6 | 0.615 | 0.179 | 0.445 | 0.059 | 0.006 | 1.232 | 0.407 | 3.820 | 0.279 | 0.564 | 4.000 | 2.000 | 0.973 | BOILING FEET_JITTER | pose tables kept |
| sw unarmed 64px | dash_SE | 5 | 0.737 | 0.361 | 0.507 | 0.145 | 0.016 | 1.258 | 0.355 | 4.225 | 0.306 | 0.684 | 7.000 | 15.000 | 0.963 | BOILING SHADE_SWAP FEET_JITTER | Argon ~8/7/7 |
| sw unarmed 64px | hurt_SE | 4 | 0.740 | 0.333 | 0.562 | 0.158 | 0.015 | 1.415 | 0.390 | 3.061 | 0.314 | 0.665 | 4.000 | 3.000 | 1.140 | BOILING FEET_JITTER | Argon ~8/7/7 |
| sw unarmed 64px | idle_SE | 6 | 0.183 | 0.064 | 0.088 | 0.007 | 0.004 | 0.156 | 0.077 | 0.387 | 0.390 | 0.229 | 1.000 | 1.000 | 0.860 | ok | Argon ~8/7/7 |
| sw unarmed 64px | jump_SE | 8 | 0.815 | 0.500 | 0.437 | 0.128 | 0.004 | 1.087 | 0.313 | 3.015 | 0.281 | 0.872 | 19.000 | 18.000 | 0.534 | BOILING FEET_JITTER | Argon ~8/7/7 |
| sw unarmed 64px | run_SE | 6 | 0.708 | 0.299 | 0.567 | 0.132 | 0.013 | 1.318 | 0.393 | 5.357 | 0.280 | 0.623 | 4.000 | 8.000 | 0.901 | BOILING FEET_JITTER | Argon ~8/7/7 |
| sw throw 64px | throw_SE | 34 | 0.243 | 0.091 | 0.065 | 0.013 | 0.003 | 0.402 | 0.098 | 2.436 | 0.468 | 0.885 | 19.000 | 23.000 | 1.084 | FEET_JITTER | Opus 5-6 |
| sw 3d_motion preview (control) | dash_SE | 5 | 0.965 | 0.893 | 0.317 | 0.266 | 0.139 | 0.260 | 0.064 | 0.764 | 0.353 | 0.838 | 20.000 | 31.000 | 0.986 | BOILING SHADE_SWAP FEET_JITTER | AA 3D render, not pixels |
| sw 3d_motion preview (control) | idle_SE | 6 | 0.753 | 0.657 | 0.119 | 0.022 | 0.390 | 0.221 | 0.077 | 0.419 | 0.245 | 0.246 | 1.000 | 17.000 | 0.928 | BOILING SHADE_SWAP | AA 3D render, not pixels |
| sw 3d_motion preview (control) | jump_SE | 8 | 0.977 | 0.900 | 0.300 | 0.236 | 0.135 | 0.278 | 0.073 | 0.741 | 0.298 | 0.946 | 111.000 | 84.000 | 0.945 | BOILING SHADE_SWAP FEET_JITTER | AA 3D render, not pixels |
| sw 3d_motion preview (control) | run_SE | 6 | 0.942 | 0.857 | 0.497 | 0.285 | 0.219 | 0.275 | 0.072 | 0.977 | 0.331 | 0.549 | 19.000 | 39.000 | 1.001 | BOILING SHADE_SWAP FEET_JITTER | AA 3D render, not pixels |
| sw 3d_motion preview (control) | slash_SE | 7 | 0.955 | 0.877 | 0.203 | 0.158 | 0.195 | 0.262 | 0.071 | 0.714 | 0.296 | 0.853 | 35.000 | 36.000 | 0.875 | BOILING SHADE_SWAP FEET_JITTER | AA 3D render, not pixels |
| sw 3d_motion preview (control) | walk_SE | 6 | 0.902 | 0.804 | 0.463 | 0.244 | 0.232 | 0.301 | 0.088 | 0.879 | 0.252 | 0.452 | 15.000 | 38.000 | 0.973 | BOILING SHADE_SWAP FEET_JITTER | AA 3D render, not pixels |
| snowpeak S4_hd v1 (shipped) | idle_S | 8 | 0.144 | 0.042 | 0.021 | 0.005 | 0.004 | 0.107 | 0.004 | 0.019 | 0.964 | 0.080 | 0.000 | 1.000 | 0.920 | STIFF | released |
| snowpeak S4_hd v1 (shipped) | idle_SE | 8 | 0.130 | 0.035 | 0.016 | 0.005 | 0.001 | 0.104 | 0.009 | 0.047 | 0.905 | 0.094 | 0.000 | 1.000 | 0.975 | STIFF | released |
| snowpeak S4_hd v1 (shipped) | idle_E | 8 | 0.112 | 0.035 | 0.013 | 0.004 | 0.003 | 0.088 | 0.011 | 0.055 | 0.864 | 0.107 | 0.000 | 1.000 | 0.862 | STIFF | released |
| snowpeak S4_hd v1 (shipped) | idle_NE | 8 | 0.096 | 0.022 | 0.008 | 0.006 | 0.000 | 0.080 | 0.003 | 0.012 | 0.968 | 0.100 | 0.000 | 1.000 | 0.966 | STIFF | released |
| snowpeak S4_hd v1 (shipped) | idle_N | 8 | 0.114 | 0.037 | 0.015 | 0.004 | 0.002 | 0.082 | 0.003 | 0.015 | 0.962 | 0.090 | 0.000 | 1.000 | 0.914 | STIFF | released |
| snowpeak S4_hd v1 (shipped) | idle_NW | 8 | 0.111 | 0.032 | 0.006 | 0.003 | 0.002 | 0.085 | 0.006 | 0.031 | 0.926 | 0.099 | 0.000 | 1.000 | 0.959 | STIFF | released |
| snowpeak S4_hd v1 (shipped) | idle_W | 8 | 0.121 | 0.038 | 0.015 | 0.004 | 0.002 | 0.096 | 0.007 | 0.037 | 0.915 | 0.119 | 0.000 | 1.000 | 0.969 | STIFF | released |
| snowpeak S4_hd v1 (shipped) | idle_SW | 8 | 0.146 | 0.043 | 0.019 | 0.007 | 0.000 | 0.112 | 0.012 | 0.059 | 0.890 | 0.103 | 0.000 | 1.000 | 0.892 | STIFF | released |
| snowpeak S4_hd v1 (shipped) | walk_S | 8 | 0.322 | 0.151 | 0.143 | 0.013 | 0.005 | 0.207 | 0.054 | 0.544 | 0.689 | 0.082 | 1.000 | 1.000 | 0.680 | ok | released |
| snowpeak S4_hd v1 (shipped) | walk_SE | 8 | 0.403 | 0.131 | 0.189 | 0.010 | 0.004 | 0.388 | 0.178 | 1.784 | 0.375 | 0.169 | 1.000 | 1.000 | 0.751 | ok | released |
| snowpeak S4_hd v1 (shipped) | walk_E | 8 | 0.360 | 0.160 | 0.189 | 0.017 | 0.007 | 0.298 | 0.142 | 1.417 | 0.330 | 0.147 | 1.000 | 2.000 | 0.754 | ok | released |
| snowpeak S4_hd v1 (shipped) | walk_NE | 8 | 0.329 | 0.136 | 0.139 | 0.010 | 0.007 | 0.295 | 0.150 | 1.498 | 0.261 | 0.175 | 1.000 | 2.000 | 0.702 | ok | released |
| snowpeak S4_hd v1 (shipped) | walk_N | 8 | 0.268 | 0.128 | 0.105 | 0.001 | 0.006 | 0.199 | 0.086 | 0.855 | 0.405 | 0.107 | 1.000 | 2.000 | 0.691 | ok | released |
| snowpeak S4_hd v1 (shipped) | walk_NW | 8 | 0.334 | 0.157 | 0.141 | 0.010 | 0.005 | 0.267 | 0.132 | 1.317 | 0.289 | 0.159 | 1.000 | 2.000 | 0.736 | ok | released |
| snowpeak S4_hd v1 (shipped) | walk_W | 8 | 0.382 | 0.164 | 0.198 | 0.017 | 0.013 | 0.329 | 0.159 | 1.592 | 0.303 | 0.156 | 1.000 | 2.000 | 0.777 | ok | released |
| snowpeak S4_hd v1 (shipped) | walk_SW | 8 | 0.440 | 0.174 | 0.201 | 0.011 | 0.008 | 0.395 | 0.177 | 1.773 | 0.367 | 0.197 | 1.000 | 1.000 | 0.643 | ok | released |
| snowpeak S4_hd v1 (shipped) | run_S | 8 | 0.604 | 0.170 | 0.275 | 0.007 | 0.007 | 0.753 | 0.277 | 3.953 | 0.401 | 0.224 | 2.000 | 3.000 | 0.727 | ok | released |
| snowpeak S4_hd v1 (shipped) | run_SE | 8 | 0.583 | 0.182 | 0.289 | 0.011 | 0.008 | 0.722 | 0.302 | 4.315 | 0.304 | 0.281 | 2.000 | 2.000 | 0.758 | ok | released |
| snowpeak S4_hd v1 (shipped) | run_E | 8 | 0.550 | 0.171 | 0.289 | 0.017 | 0.008 | 0.694 | 0.278 | 3.972 | 0.331 | 0.276 | 2.000 | 3.000 | 0.774 | ok | released |
| snowpeak S4_hd v1 (shipped) | run_NE | 8 | 0.492 | 0.149 | 0.227 | 0.008 | 0.006 | 0.583 | 0.233 | 3.332 | 0.370 | 0.263 | 2.000 | 1.000 | 0.713 | ok | released |
| snowpeak S4_hd v1 (shipped) | run_N | 8 | 0.476 | 0.162 | 0.205 | 0.008 | 0.004 | 0.515 | 0.199 | 2.844 | 0.408 | 0.210 | 1.000 | 2.000 | 0.740 | ok | released |
| snowpeak S4_hd v1 (shipped) | run_NW | 8 | 0.488 | 0.162 | 0.239 | 0.009 | 0.008 | 0.545 | 0.213 | 3.048 | 0.391 | 0.228 | 2.000 | 1.000 | 0.678 | ok | released |
| snowpeak S4_hd v1 (shipped) | run_W | 8 | 0.559 | 0.188 | 0.292 | 0.016 | 0.009 | 0.696 | 0.286 | 4.087 | 0.297 | 0.281 | 2.000 | 3.000 | 0.683 | ok | released |
| snowpeak S4_hd v1 (shipped) | run_SW | 8 | 0.598 | 0.194 | 0.286 | 0.013 | 0.011 | 0.723 | 0.293 | 4.184 | 0.333 | 0.302 | 2.000 | 2.000 | 0.722 | ok | released |

## still back-test (vs_illus = metrics.py definitions)

| case | view | ssim | ssim_b | dE | sil | bloat | line_f | face_ssim | orph | jaggies | colours | off_pal | outline_cov | l_corners | vs master ssim_b | vs master same_px |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| top1 vs illus | S | 0.864 | 0.961 | 8.975 | 0.977 | 0.977 | 0.886 | 0.752 | 26 | 10 | 16 | 0 | 0.995 | 5 | 0.869 | 0.654 |
| masters vs illus | S | 0.710 | 0.852 | 15.050 | 0.924 | 1.035 | 0.866 | 0.250 | 9 | 11 | 17 | 0 | 1.000 | 4 | - | - |
| masters vs geo src | S | 0.828 | 0.936 | 10.579 | 0.969 | 0.995 | 0.880 | 0.584 | 9 | 11 | 17 | 0 | 1.000 | 4 | - | - |
| top1 vs illus | SE | 0.827 | 0.943 | 9.622 | 0.980 | 0.982 | 0.839 | 0.775 | 13 | 6 | 15 | 0 | 1.000 | 7 | 0.762 | 0.528 |
| masters vs illus | SE | 0.609 | 0.806 | 16.362 | 0.896 | 0.961 | 0.828 | 0.460 | 10 | 13 | 17 | 0 | 1.000 | 7 | - | - |
| masters vs geo src | SE | 0.788 | 0.916 | 11.103 | 0.966 | 0.981 | 0.826 | 0.611 | 10 | 13 | 17 | 0 | 1.000 | 7 | - | - |
| top1 vs illus | E | 0.866 | 0.966 | 8.734 | 0.972 | 0.972 | 0.843 | 0.481 | 9 | 2 | 14 | 0 | 1.000 | 7 | 0.788 | 0.533 |
| masters vs illus | E | 0.589 | 0.764 | 18.286 | 0.863 | 1.030 | 0.725 | 0.189 | 4 | 8 | 17 | 0 | 1.000 | 4 | - | - |
| masters vs geo src | E | 0.842 | 0.956 | 8.783 | 0.973 | 0.980 | 0.832 | 0.422 | 4 | 8 | 17 | 0 | 1.000 | 4 | - | - |
| top1 vs illus | NE | 0.834 | 0.951 | 8.558 | 0.979 | 0.980 | 0.812 | - | 7 | 5 | 13 | 0 | 1.000 | 4 | 0.732 | 0.537 |
| masters vs illus | NE | 0.581 | 0.748 | 15.896 | 0.887 | 0.983 | 0.688 | 0.137 | 1 | 3 | 14 | 0 | 1.000 | 6 | - | - |
| masters vs geo src | NE | 0.835 | 0.950 | 7.784 | 0.973 | 0.978 | 0.792 | - | 1 | 3 | 14 | 0 | 1.000 | 6 | - | - |
| top1 vs illus | N | 0.858 | 0.965 | 7.212 | 0.973 | 0.974 | 0.866 | - | 9 | 5 | 12 | 0 | 1.000 | 2 | 0.883 | 0.708 |
| masters vs illus | N | 0.720 | 0.886 | 11.066 | 0.927 | 0.961 | 0.838 | - | 0 | 5 | 12 | 0 | 1.000 | 2 | - | - |
| masters vs geo src | N | 0.851 | 0.961 | 7.506 | 0.968 | 0.982 | 0.863 | - | 0 | 5 | 12 | 0 | 1.000 | 2 | - | - |

metrics.py cross-check: max |diff| 4.96e-05 over 15 sprites x 15 keys

