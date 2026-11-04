set -e
apt-get update -qq >/dev/null && apt-get install -y -qq python3 python3-pytest nodejs openssl >/dev/null 2>&1
echo "python $(python3 --version) node $(node --version) $(openssl version)"
T="tests/test_alertas_panel.py tests/test_dashboard_artefactos.py tests/test_dashboard_counters.py tests/test_dashboard_detector.py tests/test_dashboard_escenarios.py tests/test_dashboard_gui_contract.py tests/test_dashboard_variables.py tests/test_panel_auth.py tests/test_panel_auth_e2e.py tests/test_panel_revision_gui.py tests/test_salud_panel.py tests/test_escenario_vivo.py tests/test_historial_acciones.py"
for r in rama base; do
  echo "=== $r"; cd /$r
  extra=""; [ $r = rama ] && extra=tests/test_panel_cadena_v2.py
  python3 -m pytest $T $extra -q -p no:cacheprovider -rfEs 2>&1 | tail -16 || true
done