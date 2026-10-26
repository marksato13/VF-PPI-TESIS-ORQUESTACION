import sys, struct
sys.path.insert(0,'/home/m4rk/cyberflow/scripts/features')
import extract_multilayer_v3 as v3
out=sys.argv[1]; inputs=sorted(sys.argv[2:])
recs=[]; gh=None
for f in inputs:
    raw=open(f,'rb').read()
    m=raw[:4]
    if m==b'\xd4\xc3\xb2\xa1': en,div='<',1e6
    elif m==b'\xa1\xb2\xc3\xd4': en,div='>',1e6
    elif m==b'\x4d\x3c\xb2\xa1': en,div='<',1e9
    elif m==b'\xa1\xb2\x3c\x4d': en,div='>',1e9
    else: en,div='<',1e6
    if gh is None: gh=raw[:24]
    off=24
    while off+16<=len(raw):
        sec,frac,incl,orig=struct.unpack(en+'IIII', raw[off:off+16])
        data=raw[off+16:off+16+incl]
        recs.append((sec+frac/div, raw[off:off+16], data)); off+=16+incl
ctxs=[]; cidx=[]
for i,(ts,h,d) in enumerate(recs):
    c=v3.parse_con_contexto(ts,d)
    if c is not None: ctxs.append(c); cidx.append(i)
def _ts(k): return ctxs[k].packet.timestamp
guardados={}; dropped=set()
for j in sorted(range(len(ctxs)), key=_ts):
    a=ctxs[j]; p=a.packet
    clave=(p.protocol,p.src_ip,p.dst_ip,p.src_port,p.dst_port,a.ip_id,p.ip_length,p.tcp_seq,p.icmp_type,p.icmp_id)
    prev=guardados.get(clave)
    if prev is not None:
        b=ctxs[prev]
        if p.timestamp-b.packet.timestamp<=0.005 and abs(p.ttl-b.packet.ttl)<=1:
            if p.ttl>b.packet.ttl: dropped.add(cidx[prev]); guardados[clave]=j
            else: dropped.add(cidx[j])
            continue
    guardados[clave]=j
with open(out,'wb') as o:
    o.write(gh)
    for i,(ts,h,d) in enumerate(recs):
        if i not in dropped: o.write(h); o.write(d)
print('recs',len(recs),'dropped',len(dropped),'kept',len(recs)-len(dropped))
