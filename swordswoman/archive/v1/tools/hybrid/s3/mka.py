"""mka.py NAME 'pose description' -> action-key edit prompt (prev image first, guide second)."""
import sys
P='hybrid/S3_editchain/r1/prompts'
name, desc = sys.argv[1], sys.argv[2]
common = open(f'{P}/common.txt').read()
t = f"""Image 1 is the ACCEPTED previous drawing of this character from this exact camera angle: edit it into the next animation key pose. Keep her identical: same huge round head size, face, hair, bun and bow, costume, colours, line weight, shading, the same camera angle and the same facing direction. Image 2 is a grey 3D clay render of the new pose (pose and silhouette guide only; push the pose further for appeal). Image 3 is the master illustration (style only). Image 4 shows the energy of her action poses (energy only, not style).
NEW POSE: {desc}
Make the motion EXPRESSIVE and LIVELY like a top-quality 2D game animation key frame: clear line of action, squash and stretch, secondary motion in the bun, the bow loops, the pink ribbons, the skirt tails and the sleeves.
"""
open(f'{P}/{name}.txt','w').write(t + common.replace('STYLE + IDENTITY: exactly the same character, art style and rendering as the master illustration (image 1)', 'STYLE + IDENTITY: exactly the same character and rendering as image 1'))
