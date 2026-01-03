import urllib.request
urls = ['http://127.0.0.1:5000/','http://127.0.0.1:5000/start','http://127.0.0.1:5000/admin/exam/add','http://127.0.0.1:5000/admin/question/upload','http://127.0.0.1:5000/admin/question/template_theory']
for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent':'route-checker'})
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read(800).decode('utf-8',errors='replace')
        print(u, '->', resp.getcode())
        for l in data.splitlines()[:6]:
            print('   ', l)
    except Exception as e:
        print(u, '-> ERROR:', type(e).__name__, e)
