"""S1_redraw: one Gemini redraw per frame, ONE prompt template. Mirror space (sword in RIGHT hand), flipped back later.
usage: gen.py NAME PASS OUT.png [--model M] [--extra "text"]"""
import subprocess, sys
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
GI = ROOT + '/hybrid/S1_redraw/r1/guide_in'
FACING = {  # as seen in the MIRRORED guide image
 'S': 'facing straight toward the viewer (front view from the high camera)',
 'SE': 'in a three-quarter front view, body and face turned toward the lower LEFT of the picture',
 'E': 'in full side profile facing the LEFT side of the picture, one eye visible',
 'NE': 'in a back three-quarter view turned away from us toward the upper LEFT of the picture; we see the back of her head and only the edge of her cheek',
 'N': 'facing directly away from the viewer: full back view, back of the head, bun and bow, the long skirt tails',
 'NW': 'in a back three-quarter view turned away from us toward the upper RIGHT of the picture; we see the back of her head and only the edge of her cheek',
 'W': 'in full side profile facing the RIGHT side of the picture, one eye visible',
 'SW': 'in a three-quarter front view, body and face turned toward the lower RIGHT of the picture',
}
IDLE = ('Relaxed standing idle, feet slightly apart, arms hanging slightly away from the body. The katana hangs loosely in her RIGHT hand, '
        'blade pointing down and angled outward away from her leg, tip near the ground. Her left hand is empty.', 'calm', 'Calm half-lidded eyes, small closed mouth, pink blush.')
BEATS = {
 'walk_SE_k0': ('Walk cycle, CONTACT key: front heel just striking the ground with toe up, back foot rolling onto its toe, long stride, arms swinging opposite to the legs. The katana in her RIGHT hand swings back loosely, blade angled down and outward. Ribbons and skirt tails trail behind her.', 'calm'),
 'walk_SE_k1': ('Walk cycle, DOWN key: weight drops onto the front leg, the knee bent, her whole body is lowest here and slightly squashed, the skirt bell widens. The ribbons and skirt tails are still lifting behind from the last step. Katana loose in her RIGHT hand, blade down and outward.', 'calm'),
 'walk_SE_k2': ('Walk cycle, PASSING key: standing on one straight leg, the other foot lifted 2-3 cm and passing forward with the knee forward. Arms near the body. The skirt tails lift behind her, the ribbons flutter back. Katana loose in her RIGHT hand, blade down and outward.', 'calm'),
 'walk_SE_k3': ('Walk cycle, UP key: up on the ball of the stance foot, highest point of the bounce, body slightly stretched, the back foot pushing off with heel raised. The ribbons and skirt tails drop. Katana loose in her RIGHT hand, blade down and outward.', 'calm'),
 'slash_SE_k0': ('Sword-slash ANTICIPATION, a coiled spring: she grips the katana with BOTH hands and has pulled it far back and up behind her LEFT shoulder (tip pointing up and back), torso twisted hard away from the target, knees bent, weight sunk onto the back leg, front toe light. Her head is turned to the target with a fierce glare and chin down. The pink ribbons, sleeves and skirt tails swing out to the opposite side.', 'determined'),
 'slash_SE_k1': ('Sword-slash MID-SWING, the fastest moment: the torso is half unwound, the lunge starting (front foot sliding forward, back heel lifting); both hands swing the katana horizontally, the blade pointing straight out in front at mid-arc. The arms and wide sleeves are stretched long along the swing. The ribbons, skirt tails and sleeve cuffs still trail BEHIND the swing, pointing back where she came from. Eyes snapped wide open.', 'determined'),
 'slash_SE_k2': ('Sword-slash IMPACT, a strong frozen pose: a FULL wide lunge, front knee bent deep, back leg extended with heel lifted, body low and wide; both arms extended, the katana held level at the far end of its horizontal arc, edge leading, blade crisp and straight. The ribbons whip around in an S-curve, skirt tails flung out. Strong line of action like a fighting-game hit pose.', 'determined'),
 'slash_SE_k3': ('Sword-slash FOLLOW-THROUGH: the katana has carried past the target and drops low across her body, wrists rolled; the chest over-rotates past the hips, body rising a little out of the lunge. The pink ribbons swing OUT far past the body to the front, the sleeve cuffs flare, skirt tails swing around and the bow loops flip. Breathing out after the cut.', 'determined'),
 'jump_E_crouch': ('Jump ANTICIPATION CROUCH: deep squat, knees strongly bent, body SQUASHED low and wide, spine leaning forward, chin up with eyes on the jump; arms swung back behind her, katana in her RIGHT hand trailing back and low. The skirt bell is pushed wide.', 'determined'),
 'jump_E_apex': ('Jump APEX in mid-air (like refs leap pose): body STRETCHED and arched, chin up, the lead leg straight and the trailing leg bent back, toes pointed; arms up and out, katana in her RIGHT hand raised. The cloth FLOATS UP: skirt petals flare up, ribbons lift and float above, sleeve cuffs flare. Joyful.', 'happy'),
 'jump_E_land': ('Jump LANDING: heavy landing squash, knees bent deep and spread, body SQUASHED low and wide, spine bent forward, arms down and forward for balance, katana in her RIGHT hand low. The skirt bell flares out wide to both sides and the ribbons drop onto her shoulders. Effort.', 'effort'),
}
EXPR = {'calm': 'Calm half-lidded blue eyes, small closed mouth, pink blush.',
        'determined': 'Determined combat face: eyebrows slanted down, focused narrowed blue eyes, small firm mouth (see the expressions sheet, determined face).',
        'happy': 'Happy face: bright eyes, small open smile, blush.',
        'effort': 'Effort face: brows down, eyes squeezed slightly, small open mouth.'}
TEMPLATE = """Draw EXACTLY ONE single full-body figure (one character only, NOT a turnaround or model sheet, no extra views). Image 1 sets the pose, direction, camera and silhouette; image 2 is the same character already facing this exact direction and sets her design; image 3 sets the art style. Draw the chibi anime swordswoman in EXACTLY the art style, rendering, line quality, colours, face design and chibi proportions of images 2 and 3: soft cel-shaded chibi anime illustration, clean thin dark-brown lineart, flat 2-tone shading, a HUGE round head (head plus bun plus bow is almost half of her total height, the head is wider than her body), very large blue eyes set low on the face, small narrow body, short legs, tiny feet. Same high isometric camera as image 1 (looking down about 30 degrees, we see the top of her head).
Image 1 is a rough grey 3D guide of the same character ({passdesc}). She is {facing}. {beat} Copy image 1 EXACTLY for the direction, the pose of every limb, the position and angle of the katana, the size and position of the figure on the canvas, but draw her as a clean finished illustration like image 2, never like a 3D render. Make the pose read stronger and livelier than the guide, with clear weight, never stiff.
{dirnote}{exprref}
Costume: very dark brunette hair, heavy side-swept bangs, a HIGH round slightly messy bun on the top-back of the head, a BIG bright red two-loop ribbon bow at the base of the bun with both loops upright; tall stiff flared red collar; bare shoulders; detached red bell sleeves; dark-brown leather corset with buckled straps; two long thin pale-pink scarf ribbons in soft S-curves; asymmetric red wrap skirt, short in front with black shorts, long pointed petal-shaped tails at the back; bare legs; black strappy high-heel sandals. ONE katana only: black handle wrapped with small red diamonds, small silver guard with a little crescent hook, straight silver blade. No sheath, no scabbard, nothing on her hip or back.
{expr} No motion blur, no speed lines, no effects. Plain flat white background, no ground shadow, no text."""
DIRNOTE = {
 'E': 'Strict side profile: we see only one eye and her cheek in profile, the nose points to the picture edge. ',
 'W': 'Strict side profile: we see only one eye and her cheek in profile, the nose points to the picture edge. ',
 'NE': 'Her face is turned AWAY from us: we do NOT see her eyes; we see the back of her head, the bun, the back of the bow and her bare upper back. ',
 'NW': 'Her face is turned AWAY from us: we do NOT see her eyes; we see the back of her head, the bun, the back of the bow and her bare upper back. ',
 'N': 'We do NOT see her face at all: only the back of her head, the bun, the back of the bow, her bare upper back and the long skirt tails. ',
}
PASSDESC = {'clay': 'grey clay render', 'line': 'black line drawing of the 3D model', 'id': 'flat colour-coded part map: each colour is one part, green = hair, blue = bow, red = sword'}

def build(name, pas, space='M'):
    d = name.split('_')[1]
    if name.startswith('turn_'):
        beat, ek, _ = IDLE; ek = 'calm'
    else:
        beat, ek = BEATS[name]
    refs = [f'{GI}/{name}_{pas}_{space}.png', f'{GI}/lock_{d}_{space}.png', ROOT + '/concept/chibi_iso_v5.png']
    exprref = ''
    if ek != 'calm':
        refs.append(ROOT + '/hybrid/lock/expressions.png'); exprref = ' Image 4 is a sheet of her face expressions: use it for the face only.'
        if name.startswith('slash'):
            refs.append(ROOT + '/refs/2.png'); exprref += ' Image 5 shows the energy of her action poses (energy only, not design or direction).'
        elif name.startswith('jump'):
            refs.append(ROOT + '/refs/3.png'); exprref += ' Image 5 shows the energy of her leap (energy only, not design or direction).'
    p = TEMPLATE.format(dirnote=DIRNOTE.get(d,''), passdesc=PASSDESC[pas], facing=(FACING[d] if space=='M' else FACING[d].replace('LEFT','@').replace('RIGHT','LEFT').replace('@','RIGHT')), beat=beat, exprref=exprref, expr=('' if d in ('N','NE','NW') else EXPR[ek]))
    return p, refs

if __name__ == '__main__':
    a = sys.argv[1:]
    name, pas, out = a[0], a[1], a[2]
    model = a[a.index('--model') + 1] if '--model' in a else None
    extra = a[a.index('--extra') + 1] if '--extra' in a else ''
    space = 'O' if '--orig' in a else 'M'
    p, refs = build(name, pas, space)
    if space == 'O': p = p.replace('her RIGHT hand', 'her LEFT hand').replace('behind her LEFT shoulder', 'behind her RIGHT shoulder')
    if extra: p += ' ' + extra
    open(out.replace('.png', '_prompt.txt'), 'w').write(p + '\n\nREFS:\n' + '\n'.join(refs))
    cmd = [ROOT + '/.venv/bin/python', ROOT + '/tools/gemini.py', 'image', p, out] + refs + (['--model', model] if model else [])
    for t in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0: print(name, pas, 'ok', out); break
        print(name, pas, 'retry', r.stderr[-300:], file=sys.stderr)
