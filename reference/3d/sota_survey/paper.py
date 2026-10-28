import sys,json
for f in sys.argv[1:]:
    try: p=json.load(open(f))
    except Exception as e: print(f,"ERR"); continue
    print("###",p.get("id"),p.get("publishedAt","")[:10],p.get("title","").replace("\n"," "))
    print("  gh:",p.get("githubRepo"),"| proj:",p.get("projectPage"),"| stars:",p.get("githubStars"))
    print("  ",p.get("summary","").replace("\n"," ")[:700])
