const pptxgen = require('pptxgenjs');
const sharp = require('sharp');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const BENCHMARK = path.join(ROOT, '02-metodologia', 'validacion-interna-profesor', 'comparacion-modelos-esta-red-2026-10-14', 'img');
const ASSETS = {
  logo: path.join(ROOT, '03-entregables', 'assets', 'logo-upeu.png'),
  modelMetrics: path.join(BENCHMARK, 'MC-03-metricas.png'),
  suricataComparison: path.join(BENCHMARK, 'SUR-01-comparacion.png'),
  alerts: path.join(ROOT, '02-metodologia', 'validacion-interna-profesor', 'recorrido-ataque-2026-10-13', 'img', '01-alertas.png'),
  scores: path.join(ROOT, '02-metodologia', 'validacion-interna-profesor', 'recorrido-ataque-2026-10-13', 'img', '03-scores.png'),
  blocks: path.join(ROOT, '02-metodologia', 'validacion-interna-profesor', 'recorrido-ataque-2026-10-13', 'img', '07-bloqueos.png'),
};

const OUT = path.join(__dirname, 'CyberFlow-validacion-tecnica-Canva.pptx');
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Mark y Uziel';
pptx.company = 'CyberFlow';
pptx.subject = 'Validación técnica interna de CyberFlow';
pptx.title = 'CyberFlow | Validación técnica interna';
pptx.lang = 'es-PE';

const THEME = {
  name: 'CyberFlow',
  headFontFace: 'Cambria',
  bodyFontFace: 'Calibri',
  colors: {
    dk1: '0B1220', lt1: 'FFFFFF', dk2: '17233A', lt2: 'EEF1F8',
    accent1: '0F8A7D', accent2: '5CE1D2', accent3: 'B91C1C',
    accent4: 'F2B84B', accent5: '5B6B8C', accent6: '6D28D9',
    hlink: '0F8A7D', folHlink: '6D28D9',
  },
};

pptx.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace, lang: 'es-PE' };
pptx.defineSlideMaster({
  title: 'LIGHT',
  background: { color: 'FFFFFF' },
  objects: [
    { text: { text: 'CYBERFLOW  ·  VALIDACIÓN TÉCNICA', options: { x: 0.62, y: 0.2, w: 4.1, h: 0.2, fontFace: 'Courier New', fontSize: 9.5, bold: true, charSpacing: 1.3, color: '0F8A7D', margin: 0, isTextBox: true } } },
    { placeholder: { options: { name: 'title', type: 'title', x: 0.62, y: 0.54, w: 12.05, h: 0.58, fontFace: 'Cambria', fontSize: 29, bold: true, color: '131B2E', margin: 0 } } },
    { text: { text: 'CyberFlow', options: { x: 0.62, y: 7.12, w: 3.3, h: 0.16, fontSize: 9, color: '7B879D', margin: 0, isTextBox: true } } },
    { slideNumber: { x: 12.2, y: 7.08, w: 0.45, h: 0.2, fontSize: 9, color: '7B879D', align: 'right', margin: 0 } },
  ],
  slideNumber: { x: 12.2, y: 7.08, color: '7B879D' },
});

pptx.defineSlideMaster({
  title: 'DARK',
  background: { color: '0B1220' },
  objects: [
    { text: { text: 'CYBERFLOW  ·  VALIDACIÓN TÉCNICA', options: { x: 0.62, y: 0.2, w: 4.1, h: 0.2, fontFace: 'Courier New', fontSize: 9.5, bold: true, charSpacing: 1.3, color: '5CE1D2', margin: 0, isTextBox: true } } },
    { placeholder: { options: { name: 'title', type: 'title', x: 0.62, y: 0.54, w: 12.05, h: 0.58, fontFace: 'Cambria', fontSize: 29, bold: true, color: 'FFFFFF', margin: 0 } } },
    { text: { text: 'CyberFlow', options: { x: 0.62, y: 7.12, w: 3.3, h: 0.16, fontSize: 9, color: '8290AA', margin: 0, isTextBox: true } } },
    { slideNumber: { x: 12.2, y: 7.08, w: 0.45, h: 0.2, fontSize: 9, color: '8290AA', align: 'right', margin: 0 } },
  ],
  slideNumber: { x: 12.2, y: 7.08, color: '8290AA' },
});

const S = pptx.ShapeType;

function addText(slide, text, opts) {
  slide.addText(text, { margin: 0, isTextBox: true, valign: 'mid', ...opts });
}

function addNotes(slide, text) {
  slide.addNotes(text.normalize('NFD').replace(/[\u0300-\u036f]/g, ''));
}

function addCard(slide, x, y, w, h, fill, line = fill, radius = 0.14) {
  slide.addShape(S.roundRect, {
    x, y, w, h,
    rectRadius: radius,
    fill: { color: fill },
    line: { color: line, width: 1 },
  });
}

function addPill(slide, text, x, y, w, fill, color, line = fill) {
  slide.addShape(S.roundRect, { x, y, w, h: 0.34, rectRadius: 0.16, fill: { color: fill }, line: { color: line, width: 1 } });
  addText(slide, text, { x: x + 0.08, y: y + 0.02, w: w - 0.16, h: 0.28, fontSize: 10.5, bold: true, color, align: 'center' });
}

function addSource(slide, text, dark = false) {
  addText(slide, text, { x: 4.05, y: 7.1, w: 7.7, h: 0.18, fontSize: 8.5, color: dark ? '8290AA' : '7B879D', align: 'right' });
}

async function imageContain(file, x, y, w, h) {
  const meta = await sharp(file).metadata();
  const scale = Math.min(w / meta.width, h / meta.height);
  const iw = meta.width * scale;
  const ih = meta.height * scale;
  return { path: file, x: x + (w - iw) / 2, y: y + (h - ih) / 2, w: iw, h: ih };
}

async function imageCrop(file, x, y, w, h) {
  const meta = await sharp(file).metadata();
  const scale = Math.max(w / meta.width, h / meta.height);
  const sw = w / scale;
  const sh = h / scale;
  const sx = Math.max(0, (meta.width - sw) / 2);
  const sy = Math.max(0, (meta.height - sh) / 2);
  return { path: file, x, y, w, h, sizing: 'crop', srcRect: { x: sx, y: sy, w: sw, h: sh } };
}

function addStep(slide, n, title, sub, x, y, w, dark = false) {
  const base = dark ? '111C2E' : 'F3F6FA';
  const border = dark ? '283854' : 'D8DFEB';
  addCard(slide, x, y, w, 1.02, base, border);
  slide.addShape(S.ellipse, { x: x + 0.18, y: y + 0.18, w: 0.4, h: 0.4, fill: { color: '0F8A7D' }, line: { color: '0F8A7D' } });
  addText(slide, String(n), { x: x + 0.18, y: y + 0.18, w: 0.4, h: 0.4, fontSize: 12, bold: true, color: 'FFFFFF', align: 'center' });
  addText(slide, title, { x: x + 0.7, y: y + 0.16, w: w - 0.84, h: 0.28, fontSize: 15, bold: true, color: dark ? 'FFFFFF' : '131B2E' });
  addText(slide, sub, { x: x + 0.7, y: y + 0.5, w: w - 0.84, h: 0.3, fontSize: 10.5, color: dark ? '9EB0CA' : '5B6B8C' });
}

async function build() {
  // 1. Portada
  pptx.addSection({ title: 'Introducción' });
  let slide = pptx.addSlide({ masterName: 'DARK', sectionTitle: 'Introducción' });
  slide.background = { color: '0B1220' };
  slide.addShape(S.ellipse, { x: 9.15, y: -1.15, w: 5.4, h: 5.4, fill: { color: '0F8A7D', transparency: 72 }, line: { color: '0F8A7D', transparency: 100 } });
  slide.addShape(S.ellipse, { x: 10.65, y: 2.0, w: 3.8, h: 3.8, fill: { color: '6D28D9', transparency: 80 }, line: { color: '6D28D9', transparency: 100 } });
  for (let i = 0; i < 8; i++) {
    const x = 8.4 + (i % 4) * 1.05;
    const y = 1.0 + Math.floor(i / 4) * 2.0 + (i % 2) * 0.35;
    slide.addShape(S.ellipse, { x, y, w: 0.13, h: 0.13, fill: { color: i % 3 === 0 ? 'F2B84B' : '5CE1D2' }, line: { color: 'FFFFFF', transparency: 100 } });
    if (i > 0) slide.addShape(S.line, { x: x - 0.88, y: y + 0.06, w: 0.88, h: (i % 2 ? -0.28 : 0.28), line: { color: '37506F', width: 1.2, transparency: 20 } });
  }
  addText(slide, 'CYBERFLOW', { x: 0.76, y: 1.2, w: 6.8, h: 0.85, fontFace: 'Cambria', fontSize: 45, bold: true, color: 'FFFFFF' });
  addText(slide, 'Detección conductual y respuesta graduada\nen redes segmentadas', { x: 0.78, y: 2.12, w: 6.8, h: 1.05, fontSize: 24, color: 'D5E3F2', breakLine: false });
  addPill(slide, 'DETECTA', 0.8, 3.58, 1.4, '13343B', '8FE0EA', '2A7F8A');
  addPill(slide, 'DECIDE', 2.35, 3.58, 1.4, '13343B', '8FE0EA', '2A7F8A');
  addPill(slide, 'RESPONDE', 3.9, 3.58, 1.65, '3A1B20', 'FF9898', '7A2B34');
  addText(slide, 'Validación técnica interna', { x: 0.78, y: 4.42, w: 4.8, h: 0.42, fontSize: 18, bold: true, color: 'F2B84B' });
  addText(slide, 'Mark  ·  Uziel', { x: 0.78, y: 4.95, w: 4.8, h: 0.35, fontSize: 15, color: '9EB0CA' });
  slide.addImage(await imageContain(ASSETS.logo, 0.8, 5.72, 1.52, 0.68));
  addText(slide, 'Sistema open-source · modelo + heurísticos · feed firmado · nftables', { x: 0.78, y: 6.55, w: 8.6, h: 0.26, fontFace: 'Courier New', fontSize: 10.5, color: '8290AA' });
  addNotes(slide, 'Tiempo sugerido: 1 minuto. Presentar CyberFlow como complemento de Suricata y del firewall, no como sustituto. Anticipar que la presentación es breve y que la evidencia técnica se mostrará dentro de la GUI, Kali y la terminal.');

  // 2. Problema y objetivos
  slide = pptx.addSlide({ masterName: 'LIGHT', sectionTitle: 'Introducción' });
  slide.addText('Del problema a los objetivos', { placeholder: 'title' });
  addCard(slide, 0.68, 1.42, 5.16, 3.02, '131B2E', '131B2E');
  addText(slide, 'EL PROBLEMA', { x: 1.0, y: 1.72, w: 1.8, h: 0.28, fontFace: 'Courier New', fontSize: 10.5, bold: true, color: '5CE1D2', charSpacing: 1.1 });
  addText(slide, 'Las firmas reconocen\nlo conocido.', { x: 1.0, y: 2.15, w: 4.1, h: 0.85, fontFace: 'Cambria', fontSize: 26, bold: true, color: 'FFFFFF' });
  addText(slide, 'Pero detectar una anomalía no garantiza una respuesta oportuna ni trazable.', { x: 1.0, y: 3.22, w: 4.15, h: 0.7, fontSize: 15, color: 'C7D4E5' });
  addCard(slide, 6.12, 1.42, 6.52, 3.02, 'EAF7F5', 'B7DDD8');
  addText(slide, 'OBJETIVO GENERAL', { x: 6.48, y: 1.72, w: 2.3, h: 0.28, fontFace: 'Courier New', fontSize: 10.5, bold: true, color: '0F8A7D', charSpacing: 1.1 });
  addText(slide, 'Desarrollar y validar un sistema open-source que combine análisis conductual, heurísticos y respuesta graduada en una red segmentada.', { x: 6.48, y: 2.12, w: 5.62, h: 1.28, fontFace: 'Cambria', fontSize: 22, bold: true, color: '131B2E', valign: 'top' });
  addText(slide, 'Pregunta guía', { x: 6.48, y: 3.86, w: 1.3, h: 0.2, fontSize: 10, bold: true, color: '5B6B8C' });
  addText(slide, '¿Cómo convertir tráfico observado en una decisión verificable?', { x: 7.82, y: 3.79, w: 4.18, h: 0.34, fontSize: 11.5, italic: true, color: '0F8A7D' });
  const objectives = [
    ['01', 'Caracterizar', 'tráfico y línea base'],
    ['02', 'Evaluar', 'modelo y umbral'],
    ['03', 'Integrar', 'detección y respuesta'],
    ['04', 'Comparar', 'con Suricata'],
    ['05', 'Validar', 'con evidencia y expertos'],
  ];
  objectives.forEach((o, i) => {
    const x = 0.68 + i * 2.43;
    addCard(slide, x, 4.78, 2.18, 1.35, i === 2 ? 'EAF7F5' : 'F4F6FA', i === 2 ? 'B7DDD8' : 'DFE5EF');
    addText(slide, o[0], { x: x + 0.18, y: 4.94, w: 0.45, h: 0.28, fontFace: 'Courier New', fontSize: 11, bold: true, color: i === 2 ? '0F8A7D' : '7B879D' });
    addText(slide, o[1], { x: x + 0.18, y: 5.28, w: 1.78, h: 0.28, fontSize: 15, bold: true, color: '131B2E' });
    addText(slide, o[2], { x: x + 0.18, y: 5.63, w: 1.78, h: 0.28, fontSize: 10.5, color: '5B6B8C' });
  });
  addNotes(slide, 'Tiempo sugerido: 2 a 3 minutos. No leer los cinco objetivos completos; decir los verbos: caracterizar, evaluar, integrar, comparar y validar. Cierre: ahora mostraremos cómo cada objetivo se convirtió en una parte observable del sistema.');

  // 3. Alcance del análisis (declarado)
  slide = pptx.addSlide({ masterName: 'LIGHT', sectionTitle: 'Introducción' });
  slide.addText('Alcance del análisis', { placeholder: 'title' });
  addText(slide, 'Qué observa CyberFlow y qué queda fuera — declarado, no implícito', { x: 0.68, y: 1.16, w: 10.5, h: 0.34, fontSize: 15, color: '5B6B8C' });

  addCard(slide, 0.68, 1.62, 5.9, 4.12, 'EAF7F5', 'B7DDD8');
  addText(slide, 'ANALIZA', { x: 1.0, y: 1.9, w: 3.0, h: 0.26, fontFace: 'Courier New', fontSize: 11, bold: true, color: '0F8A7D', charSpacing: 1.1 });
  const alcanceSi = [
    ['Capas OSI: ', 'red (L3), transporte (L4) y aplicación (L7)'],
    ['Protocolo: ', 'IPv4'],
    ['Tráfico: ', 'de la LAN y el que va hacia Internet'],
    ['Captura: ', 'puerto espejo (SPAN), en paralelo — no en línea'],
    ['Respuesta: ', 'LIMIT / BLOCK aplicada en el host protegido'],
  ];
  alcanceSi.forEach((r, i) => {
    const y = 2.4 + i * 0.64;
    slide.addShape(S.ellipse, { x: 1.02, y: y + 0.08, w: 0.12, h: 0.12, fill: { color: '0F8A7D' }, line: { color: '0F8A7D' } });
    addText(slide, [{ text: r[0], options: { bold: true, color: '131B2E' } }, { text: r[1], options: { color: '2B3850' } }], { x: 1.3, y, w: 5.1, h: 0.56, fontSize: 12.5, valign: 'top' });
  });

  addCard(slide, 6.75, 1.62, 5.9, 4.12, 'F3F6FA', 'D8DFEB');
  addText(slide, 'FUERA DE ALCANCE', { x: 7.07, y: 1.9, w: 3.6, h: 0.26, fontFace: 'Courier New', fontSize: 11, bold: true, color: 'B45309', charSpacing: 1.1 });
  const alcanceNo = [
    ['Capa 2 (enlace, ARP): ', 'no se inspecciona'],
    ['IPv6: ', 'no se inspecciona — trabajo futuro'],
    ['Modo en línea: ', 'con SPAN el sensor no corta en ruta; observa en paralelo'],
  ];
  alcanceNo.forEach((r, i) => {
    const y = 2.4 + i * 0.64;
    slide.addShape(S.ellipse, { x: 7.09, y: y + 0.08, w: 0.12, h: 0.12, fill: { color: 'B45309' }, line: { color: 'B45309' } });
    addText(slide, [{ text: r[0], options: { bold: true, color: '131B2E' } }, { text: r[1], options: { color: '2B3850' } }], { x: 7.37, y, w: 5.1, h: 0.56, fontSize: 12.5, valign: 'top' });
  });

  addCard(slide, 0.68, 5.96, 11.96, 0.82, '131B2E', '131B2E');
  addText(slide, 'CyberFlow analiza L3/L4/L7 sobre IPv4 por puerto espejo (SPAN), en paralelo; la capa 2 e IPv6 quedan como trabajo futuro.', { x: 1.0, y: 6.1, w: 11.3, h: 0.54, fontSize: 13, bold: true, color: 'FFFFFF', valign: 'mid' });
  addSource(slide, 'Alcance declarado · coherente con la sección “Alcance del análisis” del panel');
  addNotes(slide, 'Tiempo sugerido: 1 minuto. Declarar el alcance de forma explicita: CyberFlow observa las capas de red, transporte y aplicacion sobre IPv4, mediante un puerto espejo SPAN y en paralelo, no en linea; por eso no corta en ruta sino que la respuesta se aplica en el host protegido. La capa 2 (ARP) e IPv6 quedan declarados como trabajo futuro. Responde a la observacion de la validacion interna sobre delimitar el alcance.');

  // 4. Entorno experimental y captura
  pptx.addSection({ title: 'Método' });
  slide = pptx.addSlide({ masterName: 'LIGHT', sectionTitle: 'Método' });
  slide.addText('Entorno experimental y captura', { placeholder: 'title' });
  addText(slide, 'Primero se levantó la red; después se construyó el detector', { x: 0.68, y: 1.16, w: 8.8, h: 0.34, fontSize: 15, color: '5B6B8C' });
  const environment = [
    ['01', 'CORE-STACK', 'Switches físicos · troncales VLAN', 'VLAN 20 usuarios · VLAN 30 DMZ · VLAN 10 gestión'],
    ['02', 'HOST ESXi', 'PG-CYBERFLOW-SPAN', 'Modo promiscuo · copia entregada a los sensores'],
    ['03', 'SENSOR', 'ens37 sin IP', 'tcpdump → anillo PCAP · Suricata → eve.json'],
  ];
  environment.forEach((item, i) => {
    const x = 0.68 + i * 4.16;
    addCard(slide, x, 1.62, 3.66, 3.3, i === 1 ? 'EAF7F5' : 'F4F6FA', i === 1 ? 'B7DDD8' : 'D8DFEB');
    slide.addShape(S.rect, { x: x + 0.22, y: 1.88, w: 3.22, h: 1.62, fill: { color: 'FFFFFF' }, line: { color: i === 1 ? '91CCC4' : 'C3CCDF', width: 1.2, dash: 'dash' } });
    slide.addShape(S.line, { x: x + 0.46, y: 2.1, w: 2.72, h: 1.18, line: { color: 'D8DFEB', width: 1 } });
    slide.addShape(S.line, { x: x + 3.18, y: 2.1, w: -2.72, h: 1.18, line: { color: 'D8DFEB', width: 1 } });
    addText(slide, 'ESPACIO PARA FOTO', { x: x + 0.58, y: 2.45, w: 2.45, h: 0.28, fontFace: 'Courier New', fontSize: 10.5, bold: true, color: '7B879D', align: 'center' });
    addText(slide, item[0], { x: x + 0.24, y: 3.77, w: 0.38, h: 0.25, fontFace: 'Courier New', fontSize: 10, bold: true, color: '0F8A7D' });
    addText(slide, item[1], { x: x + 0.7, y: 3.69, w: 2.55, h: 0.34, fontSize: 17, bold: true, color: '131B2E' });
    addText(slide, item[2], { x: x + 0.24, y: 4.12, w: 3.05, h: 0.25, fontSize: 11.5, bold: true, color: '0F8A7D' });
    addText(slide, item[3], { x: x + 0.24, y: 4.43, w: 3.1, h: 0.3, fontSize: 10.5, color: '5B6B8C' });
  });
  addCard(slide, 0.68, 5.24, 11.96, 0.78, '131B2E', '131B2E');
  addText(slide, 'VLAN 20/30', { x: 0.96, y: 5.48, w: 1.16, h: 0.24, fontFace: 'Courier New', fontSize: 11, bold: true, color: 'FFFFFF', align: 'center' });
  addText(slide, '→', { x: 2.2, y: 5.45, w: 0.35, h: 0.26, fontSize: 15, bold: true, color: '5CE1D2', align: 'center' });
  addText(slide, 'CORE-STACK', { x: 2.63, y: 5.48, w: 1.34, h: 0.24, fontFace: 'Courier New', fontSize: 11, bold: true, color: 'FFFFFF', align: 'center' });
  addText(slide, '→  copia SPAN  →', { x: 4.1, y: 5.47, w: 1.72, h: 0.24, fontSize: 11.5, color: '5CE1D2', align: 'center' });
  addText(slide, 'PG ESXi', { x: 5.95, y: 5.48, w: 1.08, h: 0.24, fontFace: 'Courier New', fontSize: 11, bold: true, color: 'FFFFFF', align: 'center' });
  addText(slide, '→', { x: 7.12, y: 5.45, w: 0.35, h: 0.26, fontSize: 15, bold: true, color: '5CE1D2', align: 'center' });
  addText(slide, 'ens37', { x: 7.56, y: 5.48, w: 0.84, h: 0.24, fontFace: 'Courier New', fontSize: 11, bold: true, color: 'FFFFFF', align: 'center' });
  addText(slide, '→', { x: 8.47, y: 5.45, w: 0.35, h: 0.26, fontSize: 15, bold: true, color: '5CE1D2', align: 'center' });
  addText(slide, 'PCAP + eve.json', { x: 8.92, y: 5.48, w: 1.82, h: 0.24, fontFace: 'Courier New', fontSize: 11, bold: true, color: 'FFFFFF', align: 'center' });
  addPill(slide, 'ABRIR GUI · RED Y CAPTURA', 10.72, 5.44, 1.68, '5CE1D2', '0B1220', '5CE1D2');
  addText(slide, 'La NIC de captura no enruta: recibe una copia del tráfico y produce dos fuentes observables.', { x: 1.55, y: 6.34, w: 10.2, h: 0.3, fontSize: 12.5, color: '5B6B8C', align: 'center' });
  addSource(slide, 'Fotos por insertar · detalle técnico en CyberFlow → Red y captura');
  addNotes(slide, 'Tiempo sugerido: 3 a 4 minutos. Insertar aquí fotos reales de los switches, del host ESXi y del sensor. Explicar VLAN 20, VLAN 30 y gestión; luego el puerto SPAN, el port group promiscuo y la NIC ens37 sin IP. Al terminar abrir en la GUI la vista Red y captura para recorrer la topología completa.');

  // 4. Método
  slide = pptx.addSlide({ masterName: 'LIGHT', sectionTitle: 'Método' });
  slide.addText('Cómo se construyó el detector', { placeholder: 'title' });
  addText(slide, 'Una cadena reproducible: datos reales de la red → modelo congelado → despliegue', { x: 0.68, y: 1.16, w: 9.5, h: 0.34, fontSize: 15, color: '5B6B8C' });
  const method = [
    ['1', 'Capturar', 'SPAN → PCAP + eve.json'],
    ['2', 'Depurar', 'sin control ni duplicados'],
    ['3', 'Particionar', 'bloques temporales + guarda'],
    ['4', 'Comparar', '7 candidatos + métricas'],
    ['5', 'Calibrar', 'umbral en validación'],
    ['6', 'Congelar', 'hash + equivalencia + despliegue'],
  ];
  method.forEach((m, i) => {
    const x = 0.68 + i * 2.08;
    addStep(slide, m[0], m[1], m[2], x, 1.78, 1.82, false);
    if (i < method.length - 1) {
      slide.addShape(S.chevron, { x: x + 1.83, y: 2.12, w: 0.22, h: 0.34, fill: { color: 'B7C2D4' }, line: { color: 'B7C2D4' } });
    }
  });
  addCard(slide, 0.68, 3.32, 3.5, 1.55, '131B2E', '131B2E');
  addText(slide, '335 202', { x: 1.0, y: 3.63, w: 1.85, h: 0.48, fontFace: 'Cambria', fontSize: 28, bold: true, color: 'FFFFFF' });
  addText(slide, 'ventanas normales', { x: 1.0, y: 4.16, w: 2.25, h: 0.28, fontSize: 12, color: '9EB0CA' });
  addCard(slide, 4.42, 3.32, 4.22, 1.55, 'EAF7F5', 'B7DDD8');
  addText(slide, '204 148', { x: 4.7, y: 3.67, w: 1.15, h: 0.4, fontFace: 'Courier New', fontSize: 15, bold: true, color: '0F8A7D', align: 'center' });
  addText(slide, '/', { x: 5.83, y: 3.67, w: 0.22, h: 0.4, fontFace: 'Courier New', fontSize: 15, bold: true, color: '0F8A7D', align: 'center' });
  addText(slide, '65 633', { x: 6.02, y: 3.67, w: 1.05, h: 0.4, fontFace: 'Courier New', fontSize: 15, bold: true, color: '0F8A7D', align: 'center' });
  addText(slide, '/', { x: 7.1, y: 3.67, w: 0.22, h: 0.4, fontFace: 'Courier New', fontSize: 15, bold: true, color: '0F8A7D', align: 'center' });
  addText(slide, '65 421', { x: 7.34, y: 3.67, w: 1.04, h: 0.4, fontFace: 'Courier New', fontSize: 15, bold: true, color: '0F8A7D', align: 'center' });
  addText(slide, 'entrenamiento  ·  validación  ·  prueba', { x: 4.85, y: 4.18, w: 3.35, h: 0.28, fontSize: 11, color: '5B6B8C', align: 'center' });
  addCard(slide, 8.88, 3.32, 3.76, 1.55, 'F4F0FF', 'D7C7F8');
  addText(slide, '31 → 28', { x: 9.22, y: 3.62, w: 1.8, h: 0.48, fontFace: 'Cambria', fontSize: 28, bold: true, color: '6D28D9' });
  addText(slide, 'extraídas → usadas por el modelo', { x: 9.22, y: 4.16, w: 2.9, h: 0.28, fontSize: 11.5, color: '5B6B8C' });
  addCard(slide, 0.68, 5.28, 11.96, 0.86, 'F3F6FA', 'D8DFEB');
  addText(slide, 'ABRIR EN CYBERFLOW', { x: 0.98, y: 5.52, w: 2.05, h: 0.25, fontFace: 'Courier New', fontSize: 10.5, bold: true, color: '0F8A7D' });
  addText(slide, 'Construcción y entrenamiento  →  partición  →  métricas  →  congelación  →  aprobación humana', { x: 3.02, y: 5.45, w: 8.95, h: 0.4, fontSize: 14, bold: true, color: '131B2E' });
  addSource(slide, 'Fuente: informe de calibración y vista “Construcción y entrenamiento”');
  addNotes(slide, 'Tiempo sugerido: 4 minutos. Explicar la prevención de fuga temporal y por qué el test no entrena. Enfatizar que el modelo no aprende en tiempo real: se entrena por lotes, se evalúa y solo una persona puede promoverlo. Al terminar, abrir la sección Construcción y entrenamiento de la GUI.');

  // 5. Benchmark de modelos sobre esta red
  slide = pptx.addSlide({ masterName: 'LIGHT', sectionTitle: 'Método' });
  slide.addText('Benchmark de modelos sobre esta red', { placeholder: 'title' });
  addText(slide, 'Mismos datos · mismos joblib congelados · sin reentrenar durante la comparación', { x: 0.68, y: 1.16, w: 9.5, h: 0.3, fontSize: 14, color: '5B6B8C' });
  addCard(slide, 0.68, 1.5, 7.24, 3.86, 'F7F9FC', 'DFE5EF');
  slide.addImage(await imageContain(ASSETS.modelMetrics, 0.82, 1.66, 6.96, 3.5));
  addCard(slide, 0.68, 5.58, 7.24, 0.72, 'F3F6FA', 'D8DFEB');
  addText(slide, 'PROTOCOLO', { x: 0.96, y: 5.82, w: 1.1, h: 0.22, fontFace: 'Courier New', fontSize: 9.5, bold: true, color: '0F8A7D' });
  addText(slide, '65 421 normales + 84 ataques  ·  umbral propio: ¿transfiere?  ·  FPR común 5 %: ¿qué arquitectura separa mejor?', { x: 2.02, y: 5.75, w: 5.55, h: 0.35, fontSize: 10.8, color: '131B2E' });
  addCard(slide, 8.18, 1.5, 4.46, 1.54, '131B2E', '131B2E');
  addText(slide, 'GANADOR EN ESTA RED', { x: 8.52, y: 1.82, w: 2.65, h: 0.24, fontFace: 'Courier New', fontSize: 10, bold: true, color: '5CE1D2' });
  addText(slide, 'IF recalibrado', { x: 8.52, y: 2.14, w: 2.7, h: 0.4, fontFace: 'Cambria', fontSize: 24, bold: true, color: 'FFFFFF' });
  addText(slide, 'Único con FPR operativo y mejor detección a igual FPR', { x: 8.52, y: 2.58, w: 3.65, h: 0.3, fontSize: 11.5, color: 'C7D4E5' });
  addCard(slide, 8.18, 3.28, 4.46, 3.02, 'EAF7F5', 'B7DDD8');
  addText(slide, 'MÉTRICA', { x: 8.5, y: 3.58, w: 1.15, h: 0.22, fontFace: 'Courier New', fontSize: 9.5, bold: true, color: '5B6B8C' });
  addText(slide, 'IF RECAL.', { x: 10.0, y: 3.58, w: 1.0, h: 0.22, fontFace: 'Courier New', fontSize: 9.5, bold: true, color: '0F8A7D', align: 'center' });
  addText(slide, 'OCSVM', { x: 11.28, y: 3.58, w: 0.92, h: 0.22, fontFace: 'Courier New', fontSize: 9.5, bold: true, color: 'B45309', align: 'center' });
  const benchmarkRows = [
    ['ROC-AUC', '0,923', '0,456'],
    ['PR-AUC', '0,203', '0,001'],
    ['FPR propio', '4,45 %', '99,57 %'],
    ['Det. @ FPR 5 %', '66,7 %', '0,0 %'],
  ];
  benchmarkRows.forEach((row, i) => {
    const y = 3.96 + i * 0.48;
    slide.addShape(S.line, { x: 8.48, y: y - 0.08, w: 3.78, h: 0, line: { color: 'C5DCD8', width: 0.8 } });
    addText(slide, row[0], { x: 8.5, y, w: 1.4, h: 0.24, fontSize: 11.5, bold: i > 1, color: '131B2E' });
    addText(slide, row[1], { x: 10.0, y, w: 1.0, h: 0.24, fontFace: 'Courier New', fontSize: 12, bold: true, color: '0F8A7D', align: 'center' });
    addText(slide, row[2], { x: 11.28, y, w: 0.92, h: 0.24, fontFace: 'Courier New', fontSize: 12, bold: true, color: i > 1 ? 'B91C1C' : 'B45309', align: 'center' });
  });
  addText(slide, 'Con prevalencia de ataque de 0,13 %, Precision y F1 no son el titular: se reportan, pero la decisión se sustenta en ROC/PR-AUC, FPR y detección a igual FPR.', { x: 8.5, y: 5.91, w: 3.7, h: 0.28, fontSize: 9.4, italic: true, color: '5B6B8C' });
  addText(slide, 'McNemar + Holm: IF recalibrado vs OCSVM/LOF, p < 0,001', { x: 1.55, y: 6.48, w: 5.55, h: 0.26, fontSize: 10.5, bold: true, color: '0F8A7D', align: 'center' });
  addText(slide, 'Conclusión: el ganador de laboratorio no transfiere; el IF aprende qué es normal aquí.', { x: 7.2, y: 6.43, w: 5.2, h: 0.34, fontSize: 11.3, bold: true, color: '131B2E', align: 'center' });
  addSource(slide, 'Benchmark 14-oct-2026 · comparación-modelos-esta-red');
  addNotes(slide, 'Tiempo sugerido: 5 minutos. Explicar primero los datos: 65 421 ventanas normales y 84 de ataque. Luego las dos comparaciones: umbral propio para medir transferencia y FPR común del 5 por ciento para comparar arquitectura. El OCSVM detecta todo solo porque marca 99,57 por ciento del tráfico normal; a FPR justo detecta cero. El IF recalibrado obtiene ROC-AUC 0,923, PR-AUC 0,203, FPR 4,45 por ciento y detección 66,7 por ciento a igual FPR.');

  // 5. GUI
  pptx.addSection({ title: 'Sistema en vivo' });
  slide = pptx.addSlide({ masterName: 'DARK', sectionTitle: 'Sistema en vivo' });
  slide.addText('CyberFlow en una sola vista', { placeholder: 'title' });
  addText(slide, 'La diapositiva orienta; la evidencia se explica en la GUI', { x: 0.68, y: 1.16, w: 7.0, h: 0.3, fontSize: 14, color: '9EB0CA' });
  addCard(slide, 0.68, 1.58, 5.78, 2.37, '111C2E', '283854');
  slide.addImage(await imageContain(ASSETS.alerts, 0.78, 1.69, 5.58, 2.15));
  addPill(slide, '1 · ALERTA', 0.92, 1.76, 1.36, '3A1B20', 'FF9898', '7A2B34');
  addCard(slide, 6.74, 1.58, 5.9, 2.37, '111C2E', '283854');
  slide.addImage(await imageContain(ASSETS.scores, 6.84, 1.69, 5.7, 2.15));
  addPill(slide, '2 · SCORE / UMBRAL', 6.98, 1.76, 2.05, '13343B', '8FE0EA', '2A7F8A');
  addCard(slide, 0.68, 4.2, 7.55, 2.2, '111C2E', '283854');
  slide.addImage(await imageContain(ASSETS.blocks, 0.8, 4.31, 7.31, 1.98));
  addPill(slide, '4 · RESPUESTA', 0.92, 4.4, 1.68, '3A1B20', 'FF9898', '7A2B34');
  addCard(slide, 8.52, 4.2, 4.12, 2.2, '13343B', '2A7F8A');
  addText(slide, 'RECORRIDO EN VIVO', { x: 8.88, y: 4.54, w: 2.6, h: 0.28, fontFace: 'Courier New', fontSize: 10.5, bold: true, color: '8FE0EA' });
  const flow = ['SPAN / PCAP + eve.json', '28 variables + conteos', 'Modelo OR heurísticos', 'PERMIT · LIMIT · BLOCK'];
  flow.forEach((t, i) => {
    slide.addShape(S.ellipse, { x: 8.9, y: 5.03 + i * 0.32, w: 0.11, h: 0.11, fill: { color: i === 3 ? 'FF6B6B' : '5CE1D2' }, line: { color: 'FFFFFF', transparency: 100 } });
    addText(slide, t, { x: 9.15, y: 4.96 + i * 0.32, w: 3.0, h: 0.22, fontSize: 11.5, bold: i === 3, color: i === 3 ? 'FF9898' : 'FFFFFF' });
  });
  addPill(slide, 'ABRIR GUI', 11.1, 1.14, 1.32, '5CE1D2', '0B1220', '5CE1D2');
  addSource(slide, 'Capturas del panel revisado · 13-oct-2026', true);
  addNotes(slide, 'Tiempo sugerido: 6 a 8 minutos. Salir de la presentación y abrir la GUI. Recorrido recomendado: Topología y flujo; Datos en vivo para mostrar PCAP y eve.json como fuentes separadas; Decisión para mostrar modelo y heurísticos; Alertas, Scores y Bloqueos. Aclarar que Bloqueos reconstruye el estado desde el registro y el feed, no consulta directamente nftables remoto.');

  // 7. Comparación con Suricata
  pptx.addSection({ title: 'Resultados' });
  slide = pptx.addSlide({ masterName: 'LIGHT', sectionTitle: 'Resultados' });
  slide.addText('Comparación honesta: precisión frente a cobertura', { placeholder: 'title' });
  addText(slide, 'Mismo PCAP para ambos · Suricata 7.0.3 + ET Open (53 013 reglas)', { x: 0.68, y: 1.16, w: 8.8, h: 0.3, fontSize: 14, color: '5B6B8C' });
  addCard(slide, 0.68, 1.5, 7.36, 4.82, 'F7F9FC', 'DFE5EF');
  slide.addImage(await imageContain(ASSETS.suricataComparison, 0.82, 1.66, 7.08, 4.5));
  addCard(slide, 8.3, 1.5, 4.34, 1.3, '131B2E', '131B2E');
  addText(slide, 'SENSOR1 · EN VIVO', { x: 8.62, y: 1.79, w: 2.0, h: 0.24, fontFace: 'Courier New', fontSize: 10, bold: true, color: '5CE1D2' });
  addText(slide, 'Suricata produce EVE para L7', { x: 8.62, y: 2.11, w: 3.42, h: 0.3, fontSize: 15, bold: true, color: 'FFFFFF' });
  addText(slide, 'Sin ruleset de alertas: es fuente del sistema, no el IDS comparador.', { x: 8.62, y: 2.43, w: 3.48, h: 0.22, fontSize: 10.5, color: 'C7D4E5' });
  addCard(slide, 8.3, 3.02, 4.34, 1.3, 'F4F6FA', 'D8DFEB');
  addText(slide, 'VM-SURICATA · COMPARADOR', { x: 8.62, y: 3.31, w: 2.7, h: 0.24, fontFace: 'Courier New', fontSize: 10, bold: true, color: '5B6B8C' });
  addText(slide, 'Replay controlado con ET Open', { x: 8.62, y: 3.63, w: 3.42, h: 0.3, fontSize: 15, bold: true, color: '131B2E' });
  addText(slide, 'El mismo tráfico elimina la ventaja de entrada y permite comparar detección.', { x: 8.62, y: 3.95, w: 3.48, h: 0.22, fontSize: 10.5, color: '5B6B8C' });
  addCard(slide, 8.3, 4.54, 4.34, 1.78, 'EAF7F5', 'B7DDD8');
  addText(slide, 'FPR MEDIDO · 14-OCT', { x: 8.62, y: 4.83, w: 2.2, h: 0.24, fontFace: 'Courier New', fontSize: 10, bold: true, color: '0F8A7D' });
  addText(slide, '0 FP ET', { x: 8.62, y: 5.16, w: 1.75, h: 0.38, fontFace: 'Cambria', fontSize: 22, bold: true, color: '15803D' });
  addText(slide, 'de firma sobre clientes legítimos', { x: 10.28, y: 5.18, w: 1.82, h: 0.3, fontSize: 10.5, color: '5B6B8C', align: 'center' });
  addText(slide, '11 alertas STREAM fueron artefactos del espejo SPAN, no amenazas. CyberFlow: modelo 4,45 % → LIMIT; heurísticos de BLOCK: 0 FP.', { x: 8.62, y: 5.65, w: 3.5, h: 0.46, fontSize: 10.2, color: '131B2E' });
  addText(slide, 'Tradeoff: Suricata es preciso ante firmas; CyberFlow amplía la cobertura sin firma y responde.', { x: 1.1, y: 6.48, w: 8.0, h: 0.27, fontSize: 11.5, bold: true, color: '0F8A7D', align: 'center' });
  addText(slide, 'Pendiente: confirmación secundaria con corrida simultánea en vivo.', { x: 9.28, y: 6.47, w: 3.0, h: 0.28, fontSize: 9.8, italic: true, color: 'B45309', align: 'center' });
  addSource(slide, 'Batería por familia + FPR benigno medido el 14-oct-2026');
  addNotes(slide, 'Tiempo sugerido: 4 minutos. Aclarar primero la arquitectura: la Suricata de Sensor1 corre en vivo como fuente de eventos EVE, pero no carga reglas de alerta. La comparación de IDS usa la VM-SURICATA con ET Open y replay del mismo PCAP. Suricata detecta Nikto con firma y cero de tres en DNS, flood y escaneo; CyberFlow detecta las cuatro familias. En tráfico benigno de clientes Suricata obtuvo cero falsos positivos de firma; CyberFlow acepta un FPR de modelo de 4,45 por ciento, pero lo acota a LIMIT. Los heurísticos de alta confianza que llevan a BLOCK tuvieron cero falsos positivos en esta medición.');

  // 8. Comparación conceptual
  slide = pptx.addSlide({ masterName: 'DARK', sectionTitle: 'Resultados' });
  slide.addText('Suricata y CyberFlow: dos enfoques complementarios', { placeholder: 'title' });
  addText(slide, 'Firmas para lo conocido · comportamiento para lo que se desvía de la normalidad', { x: 0.68, y: 1.16, w: 10.8, h: 0.34, fontSize: 14.5, color: '9EB0CA' });

  addCard(slide, 4.62, 2.2, 4.1, 2.36, '13343B', '2A7F8A');
  addText(slide, 'DOS PREGUNTAS', { x: 5.0, y: 2.55, w: 3.34, h: 0.34, fontFace: 'Courier New', fontSize: 13, bold: true, color: '5CE1D2', align: 'center' });
  addText(slide, '¿Coincide?  +  ¿Se desvía?', { x: 5.0, y: 3.02, w: 3.34, h: 0.42, fontFace: 'Cambria', fontSize: 22, bold: true, color: 'FFFFFF', align: 'center' });
  addText(slide, 'FIRMAS  +  COMPORTAMIENTO', { x: 5.12, y: 3.58, w: 3.1, h: 0.3, fontSize: 13, bold: true, color: '8FE0EA', align: 'center' });
  addText(slide, 'No se sustituyen: juntos amplían la cobertura frente a amenazas conocidas y patrones sin firma.', { x: 5.06, y: 4.0, w: 3.22, h: 0.36, fontSize: 11.3, color: 'C7D4E5', align: 'center' });

  addCard(slide, 0.68, 1.82, 3.34, 1.54, '111C2E', '283854');
  addText(slide, 'SURICATA', { x: 1.0, y: 2.12, w: 1.7, h: 0.26, fontFace: 'Courier New', fontSize: 11, bold: true, color: 'F2B84B' });
  addText(slide, 'Detección por firmas', { x: 1.0, y: 2.5, w: 2.55, h: 0.32, fontSize: 17, bold: true, color: 'FFFFFF' });
  addText(slide, 'Pregunta: ¿coincide con una regla conocida?', { x: 1.0, y: 2.9, w: 2.58, h: 0.28, fontSize: 11, color: '9EB0CA' });

  addCard(slide, 0.68, 4.1, 3.34, 1.54, '111C2E', '283854');
  addText(slide, 'FORTALEZA', { x: 1.0, y: 4.4, w: 1.7, h: 0.26, fontFace: 'Courier New', fontSize: 11, bold: true, color: 'F2B84B' });
  addText(slide, 'Precisión en lo conocido', { x: 1.0, y: 4.78, w: 2.55, h: 0.32, fontSize: 17, bold: true, color: 'FFFFFF' });
  addText(slide, 'Nikto: 1/1 · Sin firma: DNS, flood y escaneo 0/3.', { x: 1.0, y: 5.18, w: 2.58, h: 0.28, fontSize: 11, color: '9EB0CA' });

  addCard(slide, 9.3, 1.82, 3.34, 1.54, '111C2E', '283854');
  addText(slide, 'CYBERFLOW', { x: 9.62, y: 2.12, w: 1.7, h: 0.26, fontFace: 'Courier New', fontSize: 11, bold: true, color: '5CE1D2' });
  addText(slide, 'Análisis de comportamiento', { x: 9.62, y: 2.5, w: 2.55, h: 0.32, fontSize: 17, bold: true, color: 'FFFFFF' });
  addText(slide, 'Pregunta: ¿se desvía de la línea base o activa un patrón?', { x: 9.62, y: 2.9, w: 2.58, h: 0.28, fontSize: 11, color: '9EB0CA' });

  addCard(slide, 9.3, 4.1, 3.34, 1.54, '111C2E', '283854');
  addText(slide, 'FORTALEZA', { x: 9.62, y: 4.4, w: 2.2, h: 0.26, fontFace: 'Courier New', fontSize: 11, bold: true, color: '5CE1D2' });
  addText(slide, 'Cobertura sin firma', { x: 9.62, y: 4.78, w: 2.55, h: 0.32, fontSize: 17, bold: true, color: 'FFFFFF' });
  addText(slide, 'DNS, flood y escaneo: 3/3 · Respuesta LIMIT o BLOCK.', { x: 9.62, y: 5.18, w: 2.58, h: 0.28, fontSize: 11, color: '9EB0CA' });

  slide.addShape(S.chevron, { x: 4.12, y: 2.35, w: 0.36, h: 0.46, fill: { color: '3A5169' }, line: { color: '3A5169' } });
  slide.addShape(S.chevron, { x: 4.12, y: 4.63, w: 0.36, h: 0.46, fill: { color: '3A5169' }, line: { color: '3A5169' } });
  slide.addShape(S.chevron, { x: 8.84, y: 2.35, w: 0.36, h: 0.46, rotate: 180, fill: { color: '3A5169' }, line: { color: '3A5169' } });
  slide.addShape(S.chevron, { x: 8.84, y: 4.63, w: 0.36, h: 0.46, rotate: 180, fill: { color: '3A5169' }, line: { color: '3A5169' } });

  addCard(slide, 2.2, 6.14, 8.94, 0.62, '2B2410', '6E5A21');
  addText(slide, 'SURICATA: amenazas conocidas  +  CYBERFLOW: conducta sin firma  =  mayor cobertura y respuesta', { x: 2.5, y: 6.31, w: 8.34, h: 0.26, fontSize: 11.4, bold: true, color: 'F8D985', align: 'center' });
  addSource(slide, 'Comparación conceptual · no se sustituyen, se complementan', true);
  addNotes(slide, 'Tiempo sugerido: 2 minutos. Suricata pregunta si el tráfico coincide con una firma conocida; por eso es preciso y rápido cuando existe una regla aplicable. CyberFlow pregunta si el tráfico se desvía de la línea base o activa un patrón; por eso amplía la cobertura sin firma y genera LIMIT o BLOCK según la confianza. La conclusión es complementariedad, no sustitución.');

  // 9. Demo y cierre
  pptx.addSection({ title: 'Demostración' });
  slide = pptx.addSlide({ masterName: 'DARK', sectionTitle: 'Demostración' });
  slide.addText('Demo: ataque → evidencia → respuesta', { placeholder: 'title' });
  addText(slide, 'La prueba termina cuando la misma IP, hora, motivo y acción coinciden en toda la cadena', { x: 0.68, y: 1.16, w: 10.4, h: 0.34, fontSize: 14.5, color: '9EB0CA' });
  const demo = [
    ['1', 'ANTES', 'Kali confirma 443/tcp open', '13343B', '8FE0EA'],
    ['2', 'ATAQUE', 'nmap a 3000 puertos', '3A1B20', 'FF9898'],
    ['3', 'DETECCIÓN', 'port_scan + score < umbral', '2B2410', 'F2D890'],
    ['4', 'RESPUESTA', 'feed firmado → agente → nftables', '3A1B20', 'FF9898'],
    ['5', 'DESPUÉS', 'Kali confirma 443/tcp filtered', '13343B', '8FE0EA'],
  ];
  demo.forEach((d, i) => {
    const x = 0.68 + i * 2.45;
    addCard(slide, x, 1.78, 2.16, 2.06, d[3], d[3]);
    slide.addShape(S.ellipse, { x: x + 0.18, y: 1.98, w: 0.42, h: 0.42, fill: { color: d[4] }, line: { color: d[4] } });
    addText(slide, d[0], { x: x + 0.18, y: 1.98, w: 0.42, h: 0.42, fontSize: 12, bold: true, color: d[3] === '2B2410' ? '2B2410' : '0B1220', align: 'center' });
    addText(slide, d[1], { x: x + 0.18, y: 2.56, w: 1.75, h: 0.28, fontFace: 'Courier New', fontSize: 10.5, bold: true, color: d[4] });
    addText(slide, d[2], { x: x + 0.18, y: 2.95, w: 1.72, h: 0.58, fontSize: 13, bold: true, color: 'FFFFFF', valign: 'top' });
    if (i < demo.length - 1) slide.addShape(S.chevron, { x: x + 2.18, y: 2.52, w: 0.22, h: 0.4, fill: { color: '3A5169' }, line: { color: '3A5169' } });
  });
  addCard(slide, 0.68, 4.24, 7.2, 1.7, '111C2E', '283854');
  addText(slide, 'CRITERIO DE VALIDACIÓN', { x: 1.0, y: 4.58, w: 2.2, h: 0.27, fontFace: 'Courier New', fontSize: 10.5, bold: true, color: '5CE1D2' });
  addText(slide, 'GUI = motor_decision.log = feed = nftables', { x: 1.0, y: 5.02, w: 5.98, h: 0.42, fontFace: 'Cambria', fontSize: 22, bold: true, color: 'FFFFFF' });
  addCard(slide, 8.18, 4.24, 4.46, 1.7, '2B2410', '6E5A21');
  addText(slide, 'EVALUAMOS', { x: 8.52, y: 4.58, w: 1.6, h: 0.27, fontFace: 'Courier New', fontSize: 10.5, bold: true, color: 'F2D890' });
  addText(slide, 'Entorno · producto · evidencia · límites', { x: 8.52, y: 5.02, w: 3.55, h: 0.48, fontSize: 17, bold: true, color: 'FFFFFF' });
  addPill(slide, 'CAMBIAR A KALI + GUI + TERMINAL', 4.1, 6.42, 4.88, '5CE1D2', '0B1220', '5CE1D2');
  addSource(slide, 'Escenario: Kali 10.10.20.30 → srv-dmz 10.10.30.10', true);
  addNotes(slide, 'Tiempo sugerido: 8 minutos de demo y hasta 7 minutos de preguntas. Orden: comprobar 443 open; lanzar nmap; mostrar Alertas, Decisiones y Scores; esperar el ciclo del feed y agente; mostrar Bloqueos; verificar nftables directamente en srv-dmz; repetir nmap y comprobar filtered. Si algo falla, usar el video de respaldo. No decir que el panel lee nftables remoto: la prueba directa se hace en terminal. Cerrar solicitando a los expertos evaluar entorno, producto, trazabilidad y límites declarados.');

  await pptx.writeFile({ fileName: OUT });
  console.log(OUT);
}

build().catch((error) => {
  console.error(error);
  process.exit(1);
});
