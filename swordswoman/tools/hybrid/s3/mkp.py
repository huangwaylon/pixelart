"""mkp.py NAME 'facing description' ['extra'] -> prompts/NAME.txt (direction-edit template, guide first)."""
import sys
P='hybrid/S3_editchain/r1/prompts'
name, desc = sys.argv[1], sys.argv[2]; extra = sys.argv[3] if len(sys.argv) > 3 else ''
common = open(f'{P}/common.txt').read()
t = f"""Image 1 is a grey 3D clay render that defines the camera, facing direction, pose and silhouette for this drawing: the character {desc}. Image 2 is the ACCEPTED drawing of the same character from the neighbouring angle: copy her exact style, proportions, huge head size, colours, line weight and costume from it, but rotate her to image 1's angle. Image 3 is a design reference of the character from this angle. Image 4 is the master illustration (style only).
TASK: redraw the character exactly in image 1's facing direction, pose and silhouette, high isometric camera looking down about 30 degrees, relaxed idle stance, the katana hanging down at her side in the same hand and on the same side of the picture as in image 1. {extra}
"""
open(f'{P}/{name}.txt','w').write(t + common)
