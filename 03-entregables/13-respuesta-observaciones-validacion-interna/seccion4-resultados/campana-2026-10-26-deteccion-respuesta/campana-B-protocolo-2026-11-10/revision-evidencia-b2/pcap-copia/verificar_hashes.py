import hashlib, sys, pathlib
d = pathlib.Path(sys.argv[1]); mal = []; n = 0
for l in open(d / "ficheros-ventana.sha256"):
    h, f = l.split()
    n += 1
    if hashlib.sha256((d / "pcap" / f).read_bytes()).hexdigest() != h:
        mal.append(f)
print("ficheros en el manifiesto:", n, "| con hash distinto o ausentes:", len(mal), mal[:5])
