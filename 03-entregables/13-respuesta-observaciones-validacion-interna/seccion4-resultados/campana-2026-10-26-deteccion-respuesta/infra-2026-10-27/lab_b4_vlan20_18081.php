<?php
/*  lab_b4_vlan20_18081.php   (clon de PFSENSE/BIN/lab_b4_vlan20_8081.php para T3 CyberFlow)
 *
 *  Una regla en la interfaz de la VLAN 20:
 *      pass tcp  10.10.20.30 -> 10.10.30.10 : 18081
 *      descr: "T3 PPI brute-lab 18081 (temporal)"
 *
 *  POR QUE ESTE SCRIPT Y NO easyrule: easyrule anade la regla al FINAL de la
 *  interfaz, por debajo de CODEX_BASE_DENY_VLAN20_TO_VLAN30_OTHER, asi que el
 *  deny (quick) matchea primero y el pass nunca se evalua (Kali -> 000).
 *  Aqui el punto de insercion se CALCULA: primera block/reject de la interfaz
 *  cuyo destino cubra 10.10.30.10 y cuyo puerto cubra 18081 (18081 no esta en
 *  LAB_PUERTOS_CERRADOS, asi que la que ensombrece es el propio deny base).
 *  El pass va JUSTO ENCIMA. Ademas retira cualquier pass 10.10.20.30->:18081
 *  previo (p.ej. el de easyrule mal colocado), para no dejar duplicados.
 *
 *  USO:  php -f lab_b4_vlan20_18081.php            simula
 *        php -f lab_b4_vlan20_18081.php aplicar
 *        php -f lab_b4_vlan20_18081.php quitar
 */
require_once("config.inc");
require_once("util.inc");
require_once("filter.inc");

$modo = isset($argv[1]) ? strtolower($argv[1]) : 'simular';
if (!in_array($modo, array('simular', 'aplicar', 'quitar'))) {
    echo "Uso: php -f lab_b4_vlan20_18081.php [simular|aplicar|quitar]\n";
    exit(1);
}

$VLAN   = '20';
$ORIGEN = '10.10.20.30';
$DEST   = '10.10.30.10';
$PUERTO = '18081';
$DESCR  = 'T3 PPI brute-lab 18081 (temporal)';

echo "=== " . trim(shell_exec("hostname")) . " ===  modo: $modo\n\n";

/* 1. interfaz por etiqueta de VLAN -------------------------------------- */
$iface = null;
foreach ($config['interfaces'] as $k => $d) {
    if (isset($d['if']) && preg_match('/\.(\d+)$/', $d['if'], $m) && $m[1] === $VLAN) {
        $iface = $k; break;
    }
}
if (!$iface) { echo "ABORTA: no hay interfaz con etiqueta de VLAN $VLAN.\n"; exit(1); }
printf("interfaz VLAN %s : %s (%s)\n", $VLAN, $iface, $config['interfaces'][$iface]['descr']);

/* detector de cualquier pass 10.10.20.30 -> 10.10.30.10:18081 (sea cual sea su descr) */
function es_dup($r, $iface, $ORIGEN, $DEST, $PUERTO) {
    return isset($r['type']) && $r['type'] === 'pass'
        && isset($r['interface']) && $r['interface'] === $iface
        && isset($r['source']['address']) && $r['source']['address'] === $ORIGEN
        && isset($r['destination']['address']) && $r['destination']['address'] === $DEST
        && isset($r['destination']['port']) && (string)$r['destination']['port'] === (string)$PUERTO;
}

/* 2. idempotencia: ya existe NUESTRA regla (por descr) ------------------ */
foreach ($config['filter']['rule'] as $r) {
    if (isset($r['descr']) && $r['descr'] === $DESCR && $modo !== 'quitar') {
        echo "La regla '$DESCR' ya existe. No se toca nada.\n"; exit(0);
    }
}

/* 3. quitar: retira NUESTRA regla y cualquier dup 10.10.20.30->:18081 --- */
if ($modo === 'quitar') {
    $n = 0; $limpias = array();
    foreach ($config['filter']['rule'] as $r) {
        if ((isset($r['descr']) && $r['descr'] === $DESCR) || es_dup($r, $iface, $ORIGEN, $DEST, $PUERTO)) { $n++; continue; }
        $limpias[] = $r;
    }
    if ($n === 0) { echo "No habia ninguna regla a :$PUERTO. Nada que quitar.\n"; exit(0); }
    $copia = "/root/config-antes-t3-" . date('Ymd-His') . ".xml";
    copy('/cf/conf/config.xml', $copia);
    $config['filter']['rule'] = array_values($limpias);
    write_config("T3: retiradas reglas VLAN20 -> $DEST:$PUERTO");
    libxml_use_internal_errors(true);
    if (simplexml_load_file('/cf/conf/config.xml') === false) { copy($copia, '/cf/conf/config.xml'); echo "XML invalido. RESTAURADO.\n"; exit(1); }
    filter_configure();
    echo "retiradas $n regla(s). copia: $copia\n";
    exit(0);
}

/* 4. resolver un alias de puertos a su lista de numeros ----------------- */
function puertos_de($config, $valor) {
    if (ctype_digit((string)$valor)) { return array((string)$valor); }
    if (isset($config['aliases']['alias'])) {
        foreach ($config['aliases']['alias'] as $a) {
            if ($a['name'] === $valor && $a['type'] === 'port') {
                return preg_split('/\s+/', trim($a['address']));
            }
        }
    }
    return array();
}

/* 5. punto de insercion: primera block/reject que ensombreceria --------- */
$pos = null; $motivo = '';
foreach ($config['filter']['rule'] as $i => $r) {
    if (!isset($r['interface']) || $r['interface'] !== $iface) { continue; }
    if (isset($r['disabled'])) { continue; }
    if (!in_array($r['type'], array('block', 'reject'))) { continue; }

    $cubre_dest = false;
    if (isset($r['destination']['any'])) { $cubre_dest = true; }
    elseif (isset($r['destination']['address']) && $r['destination']['address'] === $DEST) { $cubre_dest = true; }
    elseif (isset($r['destination']['network'])) {
        $red = $r['destination']['network'];
        if (isset($config['interfaces'][$red]['if']) &&
            preg_match('/\.(\d+)$/', $config['interfaces'][$red]['if'], $mm) && $mm[1] === '30') {
            $cubre_dest = true;
        }
    }
    if (!$cubre_dest) { continue; }

    $cubre_pto = true;
    if (isset($r['destination']['port'])) {
        $cubre_pto = in_array($PUERTO, puertos_de($config, $r['destination']['port']));
    }
    if (!$cubre_pto) { continue; }

    $pos = $i;
    $motivo = sprintf("#%d %s -> %s%s", $i, $r['type'],
        isset($r['destination']['address']) ? $r['destination']['address']
            : (isset($r['destination']['network']) ? 'net:' . $r['destination']['network'] : 'any'),
        isset($r['destination']['port']) ? ':' . $r['destination']['port'] : '');
    break;
}
if ($pos === null) {
    echo "ABORTA: no se encontro ninguna regla que ensombrezca este trafico. Revisar a mano.\n";
    exit(1);
}
printf("se insertara JUSTO ENCIMA de: %s\n", $motivo);

/* 6. el destino responde? ----------------------------------------------- */
$vivo = false;
foreach (array(22, 80, 443, 8080, 18081) as $p) {
    $fp = @fsockopen($DEST, $p, $e, $s, 2);
    if ($fp) { $vivo = true; fclose($fp); printf("  %s:%d abierto\n", $DEST, $p); }
}
if (!$vivo) { echo "ABORTA: $DEST no responde en ningun puerto.\n"; exit(1); }

/* 7. la regla ----------------------------------------------------------- */
$regla = array(
    'type'       => 'pass',
    'interface'  => $iface,
    'ipprotocol' => 'inet',
    'protocol'   => 'tcp',
    'statetype'  => 'keep state',
    'source'      => array('address' => $ORIGEN),
    'destination' => array('address' => $DEST, 'port' => $PUERTO),
    'descr'      => $DESCR,
    'tracker'    => (string)(time() . rand(100, 999)),
    'created'    => array('time' => time(), 'username' => 'infra (T3 CyberFlow VLAN20->DMZ)'),
);
printf("\nregla: pass tcp %s -> %s:%s   [%s]\n", $ORIGEN, $DEST, $PUERTO, $DESCR);

if ($modo === 'simular') {
    $dups = 0;
    foreach ($config['filter']['rule'] as $r) { if (es_dup($r, $iface, $ORIGEN, $DEST, $PUERTO)) { $dups++; } }
    echo "  (se retiraran $dups regla(s) :$PUERTO mal colocadas, p.ej. la de easyrule)\n";
    echo "\nSIMULACION: no se ha escrito nada. Aplicar: php -f " . basename(__FILE__) . " aplicar\n";
    exit(0);
}

/* 8. escribir: inserta encima del deny y retira dups -------------------- */
$copia = "/root/config-antes-t3-" . date('Ymd-His') . ".xml";
if (!copy('/cf/conf/config.xml', $copia)) { echo "ABORTA: no se pudo copiar config.xml.\n"; exit(1); }
echo "\ncopia: $copia\n";

$antes = count($config['filter']['rule']);
$quitadas = 0;
$reglas = array();
foreach ($config['filter']['rule'] as $i => $r) {
    if ($i === $pos) { $reglas[] = $regla; }
    if (es_dup($r, $iface, $ORIGEN, $DEST, $PUERTO)) { $quitadas++; continue; }
    $reglas[] = $r;
}
$config['filter']['rule'] = array_values($reglas);
printf("reglas: %d -> %d  (dups retiradas: %d)\n", $antes, count($config['filter']['rule']), $quitadas);

write_config("T3: VLAN20 10.10.20.30 -> $DEST:$PUERTO sobre el deny base (temporal)");

libxml_use_internal_errors(true);
if (simplexml_load_file('/cf/conf/config.xml') === false) {
    copy($copia, '/cf/conf/config.xml');
    echo "XML INVALIDO tras guardar. RESTAURADA la copia.\n"; exit(1);
}
echo "XML valido.\n";
filter_configure();
echo "filtro recargado.\n";

/* 9. confirmar contra pfctl -------------------------------------------- */
echo "\n--- reglas del filtro que mencionan $PUERTO en vmx3.$VLAN ---\n";
$out = shell_exec("pfctl -sr 2>/dev/null | grep -F '$PUERTO' | grep -F 'vmx3.$VLAN'");
echo ($out !== null && trim($out) !== '') ? $out : "  (no aparece todavia; revisar)\n";
