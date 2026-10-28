import sys; sys.path.insert(0,'/tmp'); from stamplib import *
# silhouette rows from the S head (rows 8..31) reused so the skull matches S exactly
rows=[
R((10,"KKKKKK")),
R((8,"KKhHJJhhKK")),
R((2,"KKK"),(7,"KhHJJHHhhhK"),(20,"KKK")),
R((1,"KCRRK"),(7,"KhJHHHHhhhK"),(19,"KCRRRK")),
R((1,"KCRRRK"),(7,"KHHHHhhhhhK"),(18,"KCRRRRK")),
R((1,"KRRRRrK"),(7,"KhHhhhhhhhK"),(17,"KRRRRRrK")),
R((2,"KRRrrvK"),(8,"KhhhhhhhK"),(16,"KvrrRRRK")),
R((3,"KKrvvvK"),(9,"KKhhhhK"),(15,"KvvvrrKK")),
R((3,"KhhKKKKK"),(10,"KrrRK"),(14,"KKKKKhhK")),
R((2,"KhhhhhhhhKRrrKhhhhhhhhK")),
R((2,"KhJJHHHHHhrrhHHHHHHhhhK")),
R((1,"KhJJHHHHHHHhrhHHHHHHHhhK")),
] 
body=[
".KhJHHHHHHHHHHHHHHHHHHhhK.",
".KhHHHHHHHHHHHHHHHHHHHhpK.",
".KhHHHHHHHHHHHHHHHHHHHhhK.",
".KhHHHHHHHHHHHHHHHHHHHhpK.",
".KhHHHHHHHHHHHHHHHHHHHhpK.",
".KhHHHHHHHHHHHHHHHHHHHhhK.",
".KhHHHHHHHHHHHHHHHHHHHhhK.",
".KhhHHHHHHHHHHHHHHHHHhhhK.",
".KhhHHHHHHHHHHHHHHHHHhhhK.",
".KhhHHHHHHHHHHHHHHHHHhhhK.",
"..KhhHHHHHHHHHHHHHHHhhhK..",
"..KhhhHHHHHHHHHHHHHHhhhK..",
"...KhhhHHHHHHHHHHHHhhhK...",
"...KhhhhHHHHHHHHHHhhhhK...",
"....KhhhhHHHHHHHHhhhhK....",
"....KhhKhhhhhhhhhhKhhK....",
"....KhK.KKhhhhhhKK.KhK....",
".....K.....KKKK.....K.....",
]
rows+=body
# strands converge up into the bun base (12,9): hair_0 lines over hair_1
for (x,y) in [(5,25),(10,29),(15,29),(20,25)]:
    line(rows,12 if x<13 else 13,10,x,y,'h',only='H')
save('head_N.pix',rows,'facing N back view')
