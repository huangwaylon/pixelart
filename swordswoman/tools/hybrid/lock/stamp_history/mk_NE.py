import sys; sys.path.insert(0,'/tmp'); from stamplib import *
rows=[
R((5,"KKKKK")),
R((3,"KKhHJJhKK"),(15,"KKK")),
R((2,"KhHJJHHhhK"),(14,"KCRRK")),
R((2,"KhJHHHHhhhK"),(13,"KCRRRRK")),
R((2,"KHHHHhhhhhK"),(13,"KRRRRRRK")),
R((2,"KhHhhhhhhhKrK"),(13,"KRRRRrrK")),
R((3,"KhhhhhhhKvRK"),(14,"KvrrRRK")),
R((4,"KKhhhhKKvrrKKvvKK")),
R((4,"KhhhhhhhhKRrKhhhhhK")),
R((3,"KhhhhhhhhhhKrKHHHHHhhK")),
R((2,"KhhHHHhhhhhhhhHHHHHHhhhK")),
R((1,"KhhHHHHHhhhhhHHHHHHHHHhhK")),
".KhHHHHHHHhhhHHHHHHHHHhhK.",
".KhHHHHHHHHhhHHHHHHHHHHhK.",
".KhHHHHHHHHHhHHHHHHHHHHhK.",
".KhHHHHHHHHHhHHHHHHHHHHhK.",
".KhHHHHHHHHHHhHHHHHHHHHhK.",
".KhHHHHHHHHHHhHHHHHHHHHhK.",
".KhhHHHHHHHHHhHHHHHHHHHhK.",
".KhhHHHHHHHHHHhHHHHHHHhHK.",
".KhhHHHHHHHHHHhHHHHHHhHhK.",
".KhhhHHHHHHHHHhHHHHHhKmhK.",
".KhhhHHHHHHHHHhHHHHhKmsmK.",
".KhhhhHHHHHHHHhHHHHhKsmsK.",
"..KhhhHHHHHHHHhHHHhhhKsmK.",
"..KhhhhHHHHHHHhHHHhhhKssK.",
"...KhhhHHHHHHhhHHhhhKsmK..",
"...KhhhhHHHHHhHHhhhhKmK...",
"....KhhhhHHHHhHhhhhKKK....",
"....KhhKhhhhhhhhhhKhK.....",
"....KhK.KKhhhhhhKK.K......",
".....K.....KKKK...........",
]
for (x,y) in [(4,22),(10,29),(16,27)]:
    line(rows,8,9,x,y,'h',only='H')
line(rows,12,10,21,13,'h',only='H')
line(rows,5,11,8,10,'J',only='H'); line(rows,3,13,4,12,'J',only='H')
save('head_NE.pix',rows,'facing NE back three-quarter')
