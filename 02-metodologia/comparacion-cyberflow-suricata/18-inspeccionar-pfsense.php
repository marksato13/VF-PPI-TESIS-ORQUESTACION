<?php
// Auditoria de solo lectura: NO imprime config.xml ni credenciales.
$file = '/cf/conf/config.xml';
$xml = simplexml_load_file($file);
if ($xml === false) {
    fwrite(STDERR, "No se pudo leer config.xml\n");
    exit(1);
}
echo 'hostname=' . gethostname() . "\n";
foreach ($xml->interfaces->children() as $name => $entry) {
    if ((string)$entry->if === 'vmx3.60') {
        echo 'vlan60_interface=' . $name . ' if=' . (string)$entry->if . ' descr=' . (string)$entry->descr . "\n";
        $vlan60 = (string)$name;
    }
}
if (!isset($vlan60)) {
    fwrite(STDERR, "VLAN60 no encontrada\n");
    exit(1);
}
function endpoint($node) {
    foreach (['address', 'network', 'any'] as $key) {
        if (isset($node->{$key})) return $key . ':' . (string)$node->{$key};
    }
    return '(no definido)';
}
$index = 0;
foreach ($xml->filter->rule as $rule) {
    $index++;
    if ((string)$rule->interface !== $vlan60) continue;
    echo sprintf(
        "rule_index=%d type=%s proto=%s src=%s dst=%s dst_port=%s log=%s disabled=%s desc=%s\n",
        $index, (string)$rule->type, (string)$rule->protocol,
        endpoint($rule->source), endpoint($rule->destination),
        (string)$rule->destination->port, isset($rule->log) ? 'yes' : 'no',
        isset($rule->disabled) ? 'yes' : 'no', (string)$rule->descr
    );
}
$ha = $xml->hasync;
echo 'ha_sync_target=' . (string)$ha->synchronizetoip . "\n";
foreach (['synchronizerules', 'synchronizealiases', 'pfsyncenabled'] as $name) {
    echo 'ha_' . $name . '=' . (isset($ha->{$name}) ? 'set' : 'unset') . "\n";
}
echo 'ntpd_interfaces=' . (string)$xml->ntpd->interface . "\n";
