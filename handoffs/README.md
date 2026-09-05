# Handoffs

**La interfaz oficial entre agentes.** La sesión interactiva de Claude no es
memoria compartida: lo que no esté aquí, se pierde al cerrar la terminal.

| Archivo | Quién lo escribe | Quién lo lee |
|---|---|---|
| `HANDOFF-CLAUDE.md` | **Claude** tras auditar | Codex, antes de implementar |
| `HANDOFF-CODEX.md` | **Codex** si necesita decisión | Claude o el usuario |
| `../auditorias/claude/REVIEW-Rnn-*.md` | **Claude** tras revisar el diff | Codex, para corregir |
| `../auditorias/codex/RESULTADO-*.md` | **Codex** al terminar | Claude, para revisar |

Un handoff debe llevar siempre: hallazgos con evidencia reproducible ·
decisiones ya tomadas que no deben reabrirse · archivos que pueden y no pueden
tocarse · comandos ejecutados con salida literal · pendientes · riesgos.
