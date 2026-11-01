#!/usr/bin/env bash
# PASO2 b10 — bastion: copia las marcas y salidas de los episodios de la Kali al sensor (bytes exactos).
set -u
D=cf-paso2-20261101T0254Z
ssh -n kali "cat $D/episodios/marcas.jsonl" | ssh sensor1 "cat > $D/marcas-episodios.jsonl && sha256sum $D/marcas-episodios.jsonl && wc -l < $D/marcas-episodios.jsonl"
ssh -n kali "sha256sum $D/episodios/marcas.jsonl"
ssh -n kali "cd $D && tar -cf - episodios" | ssh sensor1 "mkdir -p $D/kali && tar -xf - -C $D/kali && ls $D/kali/episodios $D/kali/episodios/salidas"
