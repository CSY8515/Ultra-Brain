"use client";

import type { ChangeEvent, CSSProperties, PointerEvent as ReactPointerEvent } from "react";
import { useEffect, useRef, useState } from "react";

const CANVAS_WIDTH = 1200;
const CANVAS_HEIGHT = 760;
const STORAGE_KEY = "ultra-brain.user-custom/v2";

type DrawTool = "pen" | "pencil" | "brush" | "marker" | "airbrush" | "eraser" | "line" | "rectangle" | "circle" | "triangle" | "text" | "fill" | "select";
type UiTool = "select" | "move" | "button" | "text" | "card" | "panel" | "image" | "icon";
type Point = { x: number; y: number };
type CanvasNode = {
  id: string;
  name: string;
  kind: "component" | "text" | "image" | "stroke" | "shape";
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  opacity: number;
  visible: boolean;
  locked: boolean;
  points?: Point[];
  start?: Point;
  end?: Point;
  tool?: DrawTool;
  text?: string;
  src?: string;
};
type Revision = { id: string; name: string; createdAt: string; nodes: CanvasNode[]; background: string };
type Props = { baseTheme: string; onUseTheme: (preview: string, name: string) => void; onToast: (message: string) => void };

const UI_ACTIONS: Array<{ id: UiTool; label: string }> = [
  { id: "select", label: "선택·이동" },
  { id: "button", label: "버튼 추가" },
  { id: "text", label: "글자 추가" },
  { id: "card", label: "카드 추가" },
  { id: "panel", label: "패널 추가" },
  { id: "image", label: "그림 가져오기" },
  { id: "icon", label: "아이콘 추가" },
];
const DRAW_TOOLS: Array<{ id: DrawTool; label: string }> = [
  { id: "pen", label: "펜" },
  { id: "pencil", label: "연필" },
  { id: "brush", label: "브러시" },
  { id: "marker", label: "마커" },
  { id: "airbrush", label: "에어브러시" },
  { id: "eraser", label: "지우개" },
  { id: "line", label: "선" },
  { id: "rectangle", label: "사각형" },
  { id: "circle", label: "원" },
  { id: "triangle", label: "삼각형" },
  { id: "text", label: "글자" },
  { id: "fill", label: "채우기" },
];

function makeId(prefix: string) { return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`; }
function copyNodes(nodes: CanvasNode[]) { return nodes.map((node) => ({ ...node, points: node.points?.map((point) => ({ ...point })) })); }

function canvasPoint(event: ReactPointerEvent<HTMLCanvasElement>): Point {
  const rect = event.currentTarget.getBoundingClientRect();
  return {
    x: Math.max(0, Math.min(CANVAS_WIDTH, ((event.clientX - rect.left) / rect.width) * CANVAS_WIDTH)),
    y: Math.max(0, Math.min(CANVAS_HEIGHT, ((event.clientY - rect.top) / rect.height) * CANVAS_HEIGHT)),
  };
}

export function CanvasEditorV983({ baseTheme, onUseTheme, onToast }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<CanvasNode[]>([]);
  const activeRef = useRef<{ tool: DrawTool; points: Point[]; start: Point } | null>(null);
  const dragRef = useRef<{ id: string; start: Point; origin: Point; before: CanvasNode[] } | null>(null);
  const [nodes, setNodes] = useState<CanvasNode[]>([]);
  const [history, setHistory] = useState<CanvasNode[][]>([]);
  const [redoStack, setRedoStack] = useState<CanvasNode[][]>([]);
  const [mode, setMode] = useState<"ui" | "drawing">("ui");
  const [uiTool, setUiTool] = useState<UiTool>("select");
  const [drawTool, setDrawTool] = useState<DrawTool>("pen");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [color, setColor] = useState("#c8a55d");
  const [background, setBackground] = useState("#061011");
  const [size, setSize] = useState(8);
  const [opacity, setOpacity] = useState(1);
  const [stabilizer, setStabilizer] = useState(.35);
  const [pressureEnabled, setPressureEnabled] = useState(true);
  const [grid, setGrid] = useState(true);
  const [safeArea, setSafeArea] = useState(true);
  const [snap, setSnap] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [previewing, setPreviewing] = useState(false);
  const [draft, setDraft] = useState<CanvasNode | null>(null);
  const [inputDevice, setInputDevice] = useState("마우스 입력 대기");
  const [textValue, setTextValue] = useState("Ultra Brain");
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [revisionName, setRevisionName] = useState("UI 변경");
  const [customName, setCustomName] = useState(`${baseTheme} 사용자 UI`);

  useEffect(() => {
    try {
      const saved = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "null");
      if (saved?.nodes && Array.isArray(saved.nodes)) { nodesRef.current = saved.nodes; setNodes(saved.nodes); }
      if (saved?.background) setBackground(saved.background);
      if (saved?.revisions && Array.isArray(saved.revisions)) setRevisions(saved.revisions);
    } catch { /* local workspace is optional */ }
  }, []);

  function commit(next: CanvasNode[], message?: string) {
    setHistory((current) => [...current, copyNodes(nodesRef.current)].slice(-40));
    setRedoStack([]);
    nodesRef.current = next;
    setNodes(next);
    if (message) onToast(message);
  }

  function undo() {
    const previous = history.at(-1);
    if (!previous) return;
    setRedoStack((current) => [...current, copyNodes(nodesRef.current)]);
    setHistory((current) => current.slice(0, -1));
    nodesRef.current = previous;
    setNodes(previous);
  }

  function redo() {
    const next = redoStack.at(-1);
    if (!next) return;
    setHistory((current) => [...current, copyNodes(nodesRef.current)]);
    setRedoStack((current) => current.slice(0, -1));
    nodesRef.current = next;
    setNodes(next);
  }

  function selected() { return nodesRef.current.filter((node) => selectedIds.includes(node.id)); }

  function updateSelected(patch: Partial<CanvasNode>) {
    const next = nodesRef.current.map((node) => selectedIds.includes(node.id) && !node.locked ? { ...node, ...patch } : node);
    commit(next);
  }

  function addComponent(kind: Exclude<UiTool, "select" | "move" | "image">, point?: Point) {
    const labels: Record<string, string> = { button: "버튼", text: textValue || "글자", card: "카드", panel: "패널", icon: "아이콘" };
    const dimensions: Record<string, [number, number]> = { button: [240, 66], text: [280, 58], card: [320, 170], panel: [360, 220], icon: [72, 72] };
    const [width, height] = dimensions[kind] || [240, 66];
    const node: CanvasNode = { id: makeId(kind), name: labels[kind], kind: kind === "text" ? "text" : "component", text: kind === "text" ? textValue : undefined, x: point?.x ?? 120 + (nodesRef.current.length % 3) * 270, y: point?.y ?? 110 + (nodesRef.current.length % 4) * 120, width, height, color, opacity, visible: true, locked: false };
    commit([...nodesRef.current, node], `${labels[kind]}을(를) 추가했습니다`);
    setSelectedIds([node.id]);
  }

  function newScreen() { commit([], "새 화면을 만들었습니다"); setSelectedIds([]); setBackground("#061011"); }
  function deleteSelected() { if (selectedIds.length) { commit(nodesRef.current.filter((node) => !selectedIds.includes(node.id)), "선택한 요소를 삭제했습니다"); setSelectedIds([]); } }
  function duplicateSelected() { const copies = selected().map((node) => ({ ...node, id: makeId("copy"), name: `${node.name} 복사본`, x: node.x + 24, y: node.y + 24, locked: false })); if (copies.length) { commit([...nodesRef.current, ...copies], "선택한 요소를 복제했습니다"); setSelectedIds(copies.map((node) => node.id)); } }
  function toggleTool(next: UiTool | DrawTool) {
    if (mode === "ui") setUiTool((current) => current === next ? "select" : next as UiTool);
    else setDrawTool((current) => current === next ? "select" : next as DrawTool);
  }

  function hitNode(point: Point) {
    return [...nodesRef.current].reverse().find((node) => node.visible && point.x >= node.x - 18 && point.x <= node.x + node.width + 18 && point.y >= node.y - 18 && point.y <= node.y + node.height + 18);
  }

  function handlePointerDown(event: ReactPointerEvent<HTMLCanvasElement>) {
    if (previewing) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    const type = event.pointerType === "pen" ? "터치펜" : event.pointerType === "touch" ? "터치" : "마우스";
    setInputDevice(`${type} 입력 감지${event.pointerType === "pen" ? " · 압력 사용 가능" : ""}`);
    const point = canvasPoint(event);
    if (mode === "ui") {
      if (uiTool === "select" || uiTool === "move") {
        const hit = hitNode(point);
        setSelectedIds(hit ? [hit.id] : []);
        if (hit && !hit.locked) dragRef.current = { id: hit.id, start: point, origin: { x: hit.x, y: hit.y }, before: copyNodes(nodesRef.current) };
        return;
      }
      if (uiTool === "image") return;
      addComponent(uiTool as Exclude<UiTool, "select" | "move" | "image">, point);
      return;
    }
    if (drawTool === "fill") { setBackground(color); onToast("배경을 채웠습니다"); return; }
    if (drawTool === "text") { addComponent("text", point); return; }
    activeRef.current = { tool: drawTool, points: [point], start: point };
  }

  function handlePointerMove(event: ReactPointerEvent<HTMLCanvasElement>) {
    const point = canvasPoint(event);
    if (dragRef.current) {
      const drag = dragRef.current;
      const dx = point.x - drag.start.x;
      const dy = point.y - drag.start.y;
      const next = nodesRef.current.map((node) => node.id === drag.id && !node.locked ? { ...node, x: drag.origin.x + (snap ? Math.round(dx / 10) * 10 : dx), y: drag.origin.y + (snap ? Math.round(dy / 10) * 10 : dy) } : node);
      nodesRef.current = next;
      setNodes(next);
      return;
    }
    const active = activeRef.current;
    if (!active) return;
    const previous = active.points.at(-1) || point;
    const smooth = { x: previous.x + (point.x - previous.x) * (1 - stabilizer), y: previous.y + (point.y - previous.y) * (1 - stabilizer) };
    active.points.push(smooth);
    const pressure = pressureEnabled && event.pointerType === "pen" && event.pressure > 0 ? event.pressure : 1;
    setDraft({ id: "draft", name: "그리는 중", kind: ["pen", "pencil", "brush", "marker", "airbrush", "eraser"].includes(active.tool) ? "stroke" : "shape", x: active.start.x, y: active.start.y, width: Math.abs(point.x - active.start.x), height: Math.abs(point.y - active.start.y), start: active.start, end: point, points: active.points, tool: active.tool, color: active.tool === "eraser" ? background : color, opacity: active.tool === "airbrush" ? opacity * .2 : active.tool === "marker" ? opacity * .62 : opacity * pressure, visible: true, locked: false });
  }

  function handlePointerUp() {
    if (dragRef.current) { const before = dragRef.current.before; dragRef.current = null; setHistory((current) => [...current, before].slice(-40)); setRedoStack([]); return; }
    const active = activeRef.current;
    if (!active) return;
    const end = active.points.at(-1) || active.start;
    const node: CanvasNode = { id: makeId(active.tool), name: DRAW_TOOLS.find((item) => item.id === active.tool)?.label || "그림", kind: ["pen", "pencil", "brush", "marker", "airbrush", "eraser"].includes(active.tool) ? "stroke" : "shape", x: active.start.x, y: active.start.y, width: Math.abs(end.x - active.start.x), height: Math.abs(end.y - active.start.y), start: active.start, end, points: [...active.points], tool: active.tool, color: active.tool === "eraser" ? background : color, opacity, visible: true, locked: false };
    activeRef.current = null;
    setDraft(null);
    commit([...nodesRef.current, node], "그림을 추가했습니다");
  }

  function importImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const node: CanvasNode = { id: makeId("image"), name: file.name, kind: "image", src: String(reader.result), x: 80, y: 80, width: 620, height: 380, color, opacity: 1, visible: true, locked: false };
      commit([...nodesRef.current, node], "그림을 가져왔습니다");
      setSelectedIds([node.id]);
    };
    reader.readAsDataURL(file);
    event.target.value = "";
  }

  function saveDraft() { window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ nodes: nodesRef.current, background, revisions })); onToast("초안을 저장했습니다"); }
  function saveRevision() { const revision: Revision = { id: makeId("revision"), name: revisionName || "UI 변경", createdAt: new Date().toISOString(), nodes: copyNodes(nodesRef.current), background }; const next = [revision, ...revisions].slice(0, 24); setRevisions(next); window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ nodes: nodesRef.current, background, revisions: next })); onToast("변경 기록을 저장했습니다"); }
  function rollback(revision: Revision) { commit(copyNodes(revision.nodes), "선택한 변경 기록으로 되돌렸습니다"); setBackground(revision.background); }
  function createCustomTheme() { const canvas = canvasRef.current; if (!canvas) return; onUseTheme(canvas.toDataURL("image/png"), customName || `${baseTheme} 사용자 UI`); onToast("사용자 UI를 저장했습니다"); }

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;
    context.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    context.fillStyle = background;
    context.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    if (grid) { context.strokeStyle = "rgba(200,165,93,.13)"; context.lineWidth = 1; for (let x = 0; x <= CANVAS_WIDTH; x += 40) { context.beginPath(); context.moveTo(x, 0); context.lineTo(x, CANVAS_HEIGHT); context.stroke(); } for (let y = 0; y <= CANVAS_HEIGHT; y += 40) { context.beginPath(); context.moveTo(0, y); context.lineTo(CANVAS_WIDTH, y); context.stroke(); } }
    if (safeArea) { context.strokeStyle = "rgba(240,213,138,.42)"; context.setLineDash([10, 8]); context.strokeRect(54, 54, CANVAS_WIDTH - 108, CANVAS_HEIGHT - 108); context.setLineDash([]); }
    const paint = (node: CanvasNode) => {
      if (!node.visible) return;
      context.save(); context.globalAlpha = node.opacity; context.strokeStyle = node.color; context.fillStyle = node.color; context.lineWidth = node.size || 2; context.lineCap = "round"; context.lineJoin = "round";
      if (node.kind === "image" && node.src) { const image = new Image(); image.onload = () => context.drawImage(image, node.x, node.y, node.width, node.height); image.src = node.src; context.restore(); return; }
      if (node.kind === "stroke" && node.points?.length) { context.beginPath(); context.moveTo(node.points[0].x, node.points[0].y); node.points.slice(1).forEach((point) => context.lineTo(point.x, point.y)); context.stroke(); }
      else if (node.kind === "shape" && node.start && node.end) { const x = Math.min(node.start.x, node.end.x), y = Math.min(node.start.y, node.end.y), w = Math.abs(node.end.x - node.start.x), h = Math.abs(node.end.y - node.start.y); if (node.tool === "line") { context.beginPath(); context.moveTo(node.start.x, node.start.y); context.lineTo(node.end.x, node.end.y); context.stroke(); } else if (node.tool === "circle") context.stroke(new Path2D(`M ${x + w / 2} ${y} a ${w / 2} ${h / 2} 0 1 0 1 0`)); else if (node.tool === "triangle") { context.beginPath(); context.moveTo(x + w / 2, y); context.lineTo(x + w, y + h); context.lineTo(x, y + h); context.closePath(); context.stroke(); } else context.strokeRect(x, y, w, h); }
      else { context.fillStyle = `${node.color}22`; context.fillRect(node.x, node.y, node.width, node.height); context.strokeRect(node.x, node.y, node.width, node.height); if (node.text) { context.fillStyle = node.color; context.font = "24px sans-serif"; context.fillText(node.text, node.x + 18, node.y + 38); } }
      if (selectedIds.includes(node.id)) { context.strokeStyle = "#f0d58a"; context.setLineDash([6, 4]); context.strokeRect(node.x - 6, node.y - 6, node.width + 12, node.height + 12); context.setLineDash([]); }
      context.restore();
    };
    nodesRef.current.forEach(paint);
    if (draft) paint(draft);
  }, [nodes, background, grid, safeArea, selectedIds, draft]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) { if (!(event.ctrlKey || event.metaKey)) return; if (event.key.toLowerCase() === "z") { event.preventDefault(); event.shiftKey ? redo() : undo(); } if (event.key.toLowerCase() === "y") { event.preventDefault(); redo(); } }
    window.addEventListener("keydown", onKeyDown); return () => window.removeEventListener("keydown", onKeyDown);
  });

  const canvasStyle = { transform: `scale(${zoom}) rotate(${rotation}deg)` } as CSSProperties;
  return <div className="canvas-editor v983-canvas-editor">
    <div className="canvas-editor-header"><div><small>UI Studio · 사용자 지정 UI</small><h3>내 화면 만들기</h3><p>왼쪽의 두 도구함에서 기능을 고르고 가운데 화면에 바로 배치하세요.</p></div><div className="canvas-header-actions"><div className="canvas-mode-row"><button type="button" className={mode === "ui" ? "is-selected" : ""} onClick={() => setMode("ui")}>UI/UX 도구함</button><button type="button" className={mode === "drawing" ? "is-selected" : ""} onClick={() => setMode("drawing")}>그리기용 도구함</button></div><div className="canvas-value-row"><button type="button" onClick={undo} disabled={!history.length}>되돌리기</button><button type="button" onClick={redo} disabled={!redoStack.length}>다시 실행</button><button type="button" onClick={() => setPreviewing((value) => !value)}>{previewing ? "편집으로 돌아가기" : "미리보기"}</button><button type="button" onClick={saveDraft}>저장</button><button type="button" className="canvas-primary-action" onClick={saveRevision}>적용 기록 만들기</button></div></div></div>
    <div className="v983-device-status"><span className="health-dot" />{inputDevice}<span>· 다시 누르면 도구 해제</span></div>
    <div className="builder-workspace v983-workspace">
      <aside className="builder-tool-panel v983-tool-panels">
        <section className={`toolbox-section v983-toolbox ${mode === "ui" ? "is-active" : ""}`}><button type="button" className="toolbox-heading" onClick={() => setMode("ui")}><strong>UI/UX 도구함</strong><small>화면을 만들고 배치합니다</small></button><div className="toolbox-content"><button type="button" onClick={newScreen}>새 화면</button><label className="builder-file-action"><input type="file" accept="image/*" onChange={importImage} /><span>그림·배경 가져오기</span></label><div className="toolbox-chip-row">{UI_ACTIONS.map((item) => <button key={item.id} type="button" className={mode === "ui" && uiTool === item.id ? "is-selected" : ""} onClick={() => { setMode("ui"); if (item.id === "select" || item.id === "move") toggleTool(item.id); else if (item.id === "image") document.getElementById("v983-image-import")?.click(); else toggleTool(item.id); }}>{item.label}</button>)}</div><input id="v983-image-import" hidden type="file" accept="image/*" onChange={importImage} /><div className="toolbox-inline-actions"><button type="button" onClick={() => updateSelected({ width: (selected()[0]?.width || 240) + 24, height: (selected()[0]?.height || 66) + 12 })} disabled={!selectedIds.length}>크기 키우기</button><button type="button" onClick={duplicateSelected} disabled={!selectedIds.length}>복제</button><button type="button" onClick={deleteSelected} disabled={!selectedIds.length}>삭제</button><button type="button" onClick={() => updateSelected({ locked: !(selected()[0]?.locked) })} disabled={!selectedIds.length}>{selected()[0]?.locked ? "잠금 해제" : "잠금"}</button></div><div className="toolbox-inline-actions"><button type="button" onClick={() => setGrid((value) => !value)} className={grid ? "is-selected" : ""}>격자</button><button type="button" onClick={() => setSafeArea((value) => !value)} className={safeArea ? "is-selected" : ""}>안전 영역</button><button type="button" onClick={() => setSnap((value) => !value)} className={snap ? "is-selected" : ""}>딱 맞추기</button></div></div></section>
        <section className={`toolbox-section v983-toolbox ${mode === "drawing" ? "is-active" : ""}`}><button type="button" className="toolbox-heading" onClick={() => setMode("drawing")}><strong>그리기용 도구함</strong><small>터치펜·태블릿으로 그립니다</small></button><div className="toolbox-content"><div className="toolbox-chip-row drawing-tools">{DRAW_TOOLS.map((item) => <button key={item.id} type="button" className={mode === "drawing" && drawTool === item.id ? "is-selected" : ""} onClick={() => { setMode("drawing"); toggleTool(item.id); }}>{item.label}</button>)}</div><label>색상 <input type="color" value={color} onChange={(event) => setColor(event.target.value)} /></label><label>붓 크기 <input type="range" min="1" max="80" value={size} onChange={(event) => setSize(Number(event.target.value))} /><output>{size}</output></label><label>투명도 <input type="range" min=".1" max="1" step=".05" value={opacity} onChange={(event) => setOpacity(Number(event.target.value))} /><output>{Math.round(opacity * 100)}%</output></label><label>선 안정화 <input type="range" min="0" max=".8" step=".05" value={stabilizer} onChange={(event) => setStabilizer(Number(event.target.value))} /></label><div className="toolbox-inline-actions"><button type="button" className={pressureEnabled ? "is-selected" : ""} onClick={() => setPressureEnabled((value) => !value)}>펜 압력 {pressureEnabled ? "사용" : "끄기"}</button><button type="button" onClick={() => setRotation((value) => value - 15)}>왼쪽 회전</button><button type="button" onClick={() => setRotation((value) => value + 15)}>오른쪽 회전</button><button type="button" onClick={() => setZoom((value) => Math.max(.5, Math.min(1.4, value + .1)))}>확대</button><button type="button" onClick={() => setZoom((value) => Math.max(.5, value - .1))}>축소</button></div></div></section>
        <section className="v983-quick-settings"><strong>선택한 요소</strong><span>{selectedIds.length ? `${selectedIds.length}개 선택됨` : "요소를 선택하세요"}</span><label>글자<input value={textValue} onChange={(event) => setTextValue(event.target.value)} /></label><label>사용자 UI 이름<input value={customName} onChange={(event) => setCustomName(event.target.value)} /></label><button type="button" onClick={createCustomTheme}>사용자 UI로 저장</button></section>
      </aside>
      <div className="builder-canvas-column"><div className="canvas-toolbar"><span>{mode === "ui" ? "UI/UX 편집 중" : "그리기 편집 중"}</span><label>배경 <input type="color" value={background} onChange={(event) => setBackground(event.target.value)} /></label><label>확대 <input type="range" min=".5" max="1.4" step=".1" value={zoom} onChange={(event) => setZoom(Number(event.target.value))} /><output>{Math.round(zoom * 100)}%</output></label></div><div className="canvas-stage v983-canvas-stage" onPointerLeave={() => { if (activeRef.current) setDraft(null); }}><canvas ref={canvasRef} width={CANVAS_WIDTH} height={CANVAS_HEIGHT} style={canvasStyle} onPointerDown={handlePointerDown} onPointerMove={handlePointerMove} onPointerUp={handlePointerUp} onPointerCancel={() => { activeRef.current = null; dragRef.current = null; setDraft(null); }} aria-label="사용자 UI 작업 캔버스" />{previewing && <div className="canvas-preview-badge">미리보기 · 적용 전</div>}</div></div>
      <aside className="builder-property-panel v983-inspector"><section><div className="canvas-section-heading"><strong>레이어</strong><span>{nodes.length}개</span></div>{nodes.slice().reverse().map((node) => <button type="button" key={node.id} className={selectedIds.includes(node.id) ? "is-selected" : ""} onClick={() => setSelectedIds([node.id])}>{node.name}{node.locked ? " · 잠금" : ""}</button>)}</section><section><div className="canvas-section-heading"><strong>변경 기록</strong><span>{revisions.length}개</span></div><input value={revisionName} onChange={(event) => setRevisionName(event.target.value)} aria-label="변경 기록 이름" />{revisions.slice(0, 6).map((revision) => <button type="button" key={revision.id} onClick={() => rollback(revision)}>{revision.name}</button>)}</section></aside>
    </div>
  </div>;
}
