import sys; sys.path.insert(0,'/tmp'); from stamplib import *
exec(open('/tmp/mk_N.py').read().split('rows=[')[0])
top=[
R((3,"KKK"),(20,"KKK")),
R((2,"KCRK"),(10,"KKKKK"),(19,"KCRK")),
R((2,"KCRRK"),(8,"KKhHJJhKK"),(18,"KCRRK")),
R((1,"KCRRRK"),(7,"KhHJJHHhhK"),(18,"KRRRRK")),
R((1,"KRRRRRK"),(7,"KhJHHHHhhhK"),(18,"KRRRRRK")),
R((1,"KRRRRrrK"),(8,"KHHHHhhhK"),(16,"KrrRRRRK")),
R((2,"KRRrrvvK"),(9,"KhhhhhK"),(15,"KvvrrRRK")),
R((3,"KKrvvvvK"),(10,"KhhhK"),(14,"KvvvvrKK")),
R((3,"KhhKKKKKKrRrKKKKKKhhK")),
R((2,"KhhhhhhhhKRrrKhhhhhhhhK")),
R((2,"KhJJHHHHHhrrhHHHHHHhhhK")),
R((1,"KhJJHHHHHHHhrhHHHHHHHhhK")),
]
src=open('/tmp/mk_N.py').read()
body=eval(src.split('body=')[1].split(']\n')[0]+']')
rows=top+[b.replace('p','h') for b in body]
for (x,y) in [(5,26),(10,29),(15,29),(20,26)]:
    line(rows,12 if x<13 else 13,12,x,y,'h',only='H')
save('head_N.pix',rows,'facing N back view (bow loops rise above the bun)')
