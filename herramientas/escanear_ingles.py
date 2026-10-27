# Cuenta frases inglesas (ASCII con espacios) por archivo, para localizar dónde vive el texto.
import os,re,sys,collections
pat=re.compile(rb'[A-Za-z][\x20-\x7e]{10,}')
res=[]
for raiz in sys.argv[1:]:
    for dp,_,fs in os.walk(raiz):
        for f in fs:
            p=os.path.join(dp,f)
            if p.endswith('.dds'): continue
            b=open(p,'rb').read()
            m=[x for x in pat.findall(b) if b' ' in x and re.search(rb'[a-z]{3} [a-z]',x)]
            if m: res.append((sum(len(x) for x in m),len(m),p,m[0][:60]))
res.sort(reverse=True)
tot=sum(r[0] for r in res); print('TOTAL letras',tot,'archivos',len(res))
for r in res[:int(os.environ.get('N','40'))]: print(r)
