set -e
apt-get update -qq >/dev/null && apt-get install -y -qq python3 python3-pytest nodejs openssl >/dev/null 2>&1
echo "python $(python3 --version) node $(node --version) $(openssl version)"
T="tests/test_alertas_panel.py tests/test_dashboard_artefactos.py tests/test_dashboard_counters.py tests/test_dashboard_detector.py tests/test_dashboard_escenarios.py tests/test_dashboard_gui_contract.py tests/test_dashboard_variables.py tests/test_panel_auth.py tests/test_panel_auth_e2e.py tests/test_panel_revision_gui.py tests/test_salud_panel.py tests/test_escenario_vivo.py tests/test_historial_acciones.py tests/test_panel_cadena_v2.py tests/test_panel_cadena_v2_cobertura.py"
echo "=== RAMA (corrección)"; cd /rama
python3 -m pytest $T -q -p no:cacheprovider -rfEs 2>&1 | tail -25 || true
echo "=== a27889d con las regresiones nuevas (deben FALLAR)"
cp /rama/tests/test_panel_cadena_v2_cobertura.py /base/tests/
cd /base
python3 -m pytest tests/test_panel_cadena_v2_cobertura.py -q -p no:cacheprovider -rf 2>&1 | grep -E '^(FAILED|ERROR|PASSED)|passed|failed' | tail -40 || true
