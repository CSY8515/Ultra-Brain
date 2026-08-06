"use client";

import type { ChangeEvent, PointerEvent as ReactPointerEvent } from "react";
import { useCallback, useEffect, useRef, useState } from "react";

const CANVAS_WIDTH = 1200;
const CANVAS_HEIGHT = 760;
const CUSTOM_REGISTRY_KEY = "ultra-brain.user-custom/v1";

type Tool = "select" | "pen" | "brush" | "eraser" | "line" | "rectangle" | "circle" | "triangle" | "text" | "fill" | "gradient";
type Point = { x: number; y: number };
type CanvasNode = {
  id: string;
  name: string;
  kind: "stroke" | "shape" | "text" | "image" | "component";
  tool?: Tool;
  points?: Point[];
  start?: Point;
  end?: Point;
  text?: string;
  component?: string;
  src?: string;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  rotation?: number;
  group?: string;
  color: string;
  size: number;
  opacity: number;
  visible: boolean;
  locked: boolean;
};
type UserCustomTheme = { id: string; name: string; baseTheme: string; preview: string; createdAt: string; status: "draft" | "active" | "archived" };

type CanvasEditorProps = {
  baseTheme: string;
  onUseTheme: (preview: string, name: string) => void;
  onToast: (message: string) => void;
};

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

function getPoint(event: ReactPointerEvent<HTMLCanvasElement>) {
  const rect = event.currentTarget.getBoundingClientRect();
  return {
    x: Math.max(0, Math.min(CANVAS_WIDTH, ((event.clientX - rect.left) / rect.width) * CANVAS_WIDTH)),
    y: Math.max(0, Math.min(CANVAS_HEIGHT, ((event.clientY - rect.top) / rect.height) * CANVAS_HEIGHT)),
  };
}

export function CanvasEditor({ baseTheme, onUseTheme, onToast }: CanvasEditorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<CanvasNode[]>([]);
  const activeRef = useRef<{ tool: Tool; start: Point; points: Point[] } | null>(null);
  const [nodes, setNodes] = useState<CanvasNode[]>([]);
  const [history, setHistory] = useState<CanvasNode[][]>([]);
  const [redoStack, setRedoStack] = useState<CanvasNode[][]>([]);
  const [tool, setTool] = useState<Tool>("pen");
  const [color, setColor] = useState("#c8a55d");
  const [size, setSize] = useState(8);
  const [opacity, setOpacity] = useState(1);
  const [background, setBackground] = useState("#061011");
  const [grid, setGrid] = useState(true);
  const [snap, setSnap] = useState(false);
  const [safeArea, setSafeArea] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [previewMode, setPreviewMode] = useState<"desktop" | "mobile" | "full">("desktop");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [textValue, setTextValue] = useState("Ultra Brain");
  const [assetName, setAssetName] = useState("Imported image");
  const [customName, setCustomName] = useState("My Custom World");
  const [customThemes, setCustomThemes] = useState<UserCustomTheme[]>([]);
  const dragNodeRef = useRef<{ id: string; start: Point; origin: Point } | null>(null);

  useEffect(() => {
    try {
      const saved = JSON.parse(window.localStorage.getItem(CUSTOM_REGISTRY_KEY) || "[]");
      if (Array.isArray(saved)) setCustomThemes(saved);
    } catch {
      // User Custom registry is local and optional.
    }
  }, []);

  const drawScene = useCallback((nextNodes = nodesRef.current, draft?: CanvasNode) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;
    context.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    if (background.startsWith("linear-gradient")) {
      const gradient = context.createLinearGradient(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
      gradient.addColorStop(0, color);
      gradient.addColorStop(1, "#050909");
      context.fillStyle = gradient;
    } else {
      context.fillStyle = background;
    }
    context.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    for (const node of [...nextNodes, ...(draft ? [draft] : [])]) {
      if (!node.visible) continue;
      context.save();
      context.globalAlpha = node.opacity;
      if (node.kind === "image" && node.src) {
        const image = new Image();
        image.onload = () => {
          context.save();
          context.globalAlpha = node.opacity;
          const x = node.x || 0;
          const y = node.y || 0;
          const width = node.width || 420;
          const height = node.height || 280;
          context.translate(x + width / 2, y + height / 2);
          context.rotate(((node.rotation || 0) * Math.PI) / 180);
          context.drawImage(image, -width / 2, -height / 2, width, height);
          context.restore();
        };
        image.src = node.src;
      } else if (node.kind === "text") {
        context.fillStyle = node.color;
        context.font = `600 ${Math.max(12, node.size * 4)}px Georgia, serif`;
        context.fillText(node.text || "Text", node.x || 0, node.y || 0);
      } else if (node.kind === "component") {
        const x = node.x || 0;
        const y = node.y || 0;
        const width = node.width || 250;
        const height = node.height || 72;
        context.fillStyle = "rgba(6, 18, 18, .82)";
        context.strokeStyle = node.color;
        context.lineWidth = Math.max(1, node.size / 2);
        context.translate(x + width / 2, y + height / 2);
        context.rotate(((node.rotation || 0) * Math.PI) / 180);
        context.translate(-(x + width / 2), -(y + height / 2));
        context.beginPath();
        context.roundRect(x, y, width, height, 12);
        context.fill();
        context.stroke();
        context.fillStyle = node.color;
        context.font = `600 ${Math.max(14, node.size * 2)}px Pretendard, sans-serif`;
        context.fillText(node.component || node.name, x + 18, y + height / 2 + 6);
      } else if (node.kind === "shape" && node.start && node.end) {
        const start = node.start;
        const end = node.end;
        context.strokeStyle = node.color;
        context.lineWidth = node.size;
        context.lineCap = "round";
        context.beginPath();
        if (node.tool === "line") {
          context.moveTo(start.x, start.y);
          context.lineTo(end.x, end.y);
        } else if (node.tool === "rectangle") {
          context.rect(start.x, start.y, end.x - start.x, end.y - start.y);
        } else if (node.tool === "circle") {
          const radius = Math.hypot(end.x - start.x, end.y - start.y);
          context.arc(start.x, start.y, radius, 0, Math.PI * 2);
        } else {
          context.moveTo(start.x, end.y);
          context.lineTo((start.x + end.x) / 2, start.y);
          context.lineTo(end.x, end.y);
          context.closePath();
        }
        context.stroke();
      } else if (node.kind === "stroke" && node.points?.length) {
        context.globalCompositeOperation = node.tool === "eraser" ? "destination-out" : "source-over";
        context.strokeStyle = node.color;
        context.lineWidth = node.tool === "brush" ? node.size * 2.2 : node.size;
        context.lineCap = "round";
        context.lineJoin = "round";
        context.beginPath();
        node.points.forEach((point, index) => index ? context.lineTo(point.x, point.y) : context.moveTo(point.x, point.y));
        context.stroke();
      }
      context.restore();
    }
    context.save();
    if (grid) {
      context.strokeStyle = "rgba(200,165,93,.12)";
      context.lineWidth = 1;
      for (let x = 0; x <= CANVAS_WIDTH; x += 40) { context.beginPath(); context.moveTo(x, 0); context.lineTo(x, CANVAS_HEIGHT); context.stroke(); }
      for (let y = 0; y <= CANVAS_HEIGHT; y += 40) { context.beginPath(); context.moveTo(0, y); context.lineTo(CANVAS_WIDTH, y); context.stroke(); }
    }
    if (safeArea) {
      context.setLineDash([10, 8]);
      context.strokeStyle = "rgba(240,213,138,.64)";
      context.strokeRect(64, 52, CANVAS_WIDTH - 128, CANVAS_HEIGHT - 104);
      context.setLineDash([]);
    }
    context.restore();
  }, [background, grid, safeArea]);

  useEffect(() => { nodesRef.current = nodes; drawScene(nodes); }, [nodes, drawScene]);

  function commitNodes(next: CanvasNode[]) {
    setHistory((previous) => [...previous, nodesRef.current].slice(-30));
    setRedoStack([]);
    nodesRef.current = next;
    setNodes(next);
    drawScene(next);
  }

  function finishStroke(event: ReactPointerEvent<HTMLCanvasElement>) {
    const active = activeRef.current;
    if (!active) return;
    const end = getPoint(event);
    const points = [...active.points, end].map((point) => snap ? { x: Math.round(point.x / 10) * 10, y: Math.round(point.y / 10) * 10 } : point);
    const node: CanvasNode = active.tool === "pen" || active.tool === "brush" || active.tool === "eraser"
      ? { id: makeId("stroke"), name: active.tool, kind: "stroke", tool: active.tool, points, color, size, opacity, visible: true, locked: false }
      : { id: makeId("shape"), name: active.tool, kind: "shape", tool: active.tool, start: active.start, end, color, size, opacity, visible: true, locked: false };
    activeRef.current = null;
    commitNodes([...nodesRef.current, node]);
  }

  function handlePointerDown(event: ReactPointerEvent<HTMLCanvasElement>) {
    event.currentTarget.setPointerCapture(event.pointerId);
    const point = getPoint(event);
    if (tool === "select") {
      const hit = [...nodesRef.current].reverse().find((node) => {
        const x = node.x ?? node.start?.x ?? node.points?.[0]?.x ?? 0;
        const y = node.y ?? node.start?.y ?? node.points?.[0]?.y ?? 0;
        const width = node.width ?? Math.max(34, Math.abs((node.end?.x ?? x) - x));
        const height = node.height ?? Math.max(34, Math.abs((node.end?.y ?? y) - y));
        return point.x >= x - 20 && point.x <= x + width + 20 && point.y >= y - 20 && point.y <= y + height + 20;
      });
      setSelectedId(hit?.id || null);
      if (hit && !hit.locked) dragNodeRef.current = { id: hit.id, start: point, origin: { x: hit.x ?? hit.start?.x ?? 0, y: hit.y ?? hit.start?.y ?? 0 } };
      return;
    }
    if (tool === "fill") { setBackground(color); onToast("배경을 채웠습니다"); return; }
    if (tool === "gradient") { setBackground(`linear-gradient(135deg, ${color}, #050909 72%)`); onToast("그라디언트를 적용했습니다"); return; }
    if (tool === "text") { commitNodes([...nodesRef.current, { id: makeId("text"), name: textValue || "Text", kind: "text", text: textValue || "Text", x: point.x, y: point.y, color, size, opacity, visible: true, locked: false }]); return; }
    activeRef.current = { tool, start: point, points: [point] };
  }

  function handlePointerMove(event: ReactPointerEvent<HTMLCanvasElement>) {
    const nodeDrag = dragNodeRef.current;
    if (nodeDrag) {
      const point = getPoint(event);
      const dx = point.x - nodeDrag.start.x;
      const dy = point.y - nodeDrag.start.y;
      const next = nodesRef.current.map((node) => node.id === nodeDrag.id && !node.locked ? { ...node, x: nodeDrag.origin.x + dx, y: nodeDrag.origin.y + dy } : node);
      nodesRef.current = next;
      setNodes(next);
      return;
    }
    const active = activeRef.current;
    if (!active) return;
    const point = getPoint(event);
    active.points.push(point);
    const draft: CanvasNode = active.tool === "pen" || active.tool === "brush" || active.tool === "eraser"
      ? { id: "draft", name: "draft", kind: "stroke", tool: active.tool, points: active.points, color, size, opacity, visible: true, locked: false }
      : { id: "draft", name: "draft", kind: "shape", tool: active.tool, start: active.start, end: point, color, size, opacity, visible: true, locked: false };
    drawScene(nodesRef.current, draft);
  }

  function undo() {
    const previous = history.at(-1);
    if (!previous) return;
    setRedoStack((current) => [...current, nodesRef.current]);
    setHistory((current) => current.slice(0, -1));
    nodesRef.current = previous;
    setNodes(previous);
  }

  function redo() {
    const next = redoStack.at(-1);
    if (!next) return;
    setHistory((current) => [...current, nodesRef.current]);
    setRedoStack((current) => current.slice(0, -1));
    nodesRef.current = next;
    setNodes(next);
  }

  function clearCanvas() {
    if (!nodesRef.current.length) return;
    commitNodes([]);
    setSelectedId(null);
    onToast("Canvas를 비웠습니다");
  }

  function moveSelected(direction: -1 | 1) {
    if (!selectedId) return;
    const index = nodesRef.current.findIndex((node) => node.id === selectedId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= nodesRef.current.length) return;
    const next = [...nodesRef.current];
    [next[index], next[target]] = [next[target], next[index]];
    commitNodes(next);
  }

  function addComponent(component: string) {
    const node: CanvasNode = { id: makeId("component"), name: component, kind: "component", component, x: 80 + (nodesRef.current.length % 3) * 280, y: 90 + (nodesRef.current.length % 4) * 120, width: 250, height: 72, color, size: 8, opacity, visible: true, locked: false };
    commitNodes([...nodesRef.current, node]);
    setSelectedId(node.id);
  }

  function importAsset(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const src = String(reader.result);
      const node: CanvasNode = { id: makeId("image"), name: assetName || file.name, kind: "image", src, x: 160, y: 130, width: 520, height: 330, rotation: 0, color, size, opacity, visible: true, locked: false };
      commitNodes([...nodesRef.current, node]);
      onToast("이미지를 Canvas에 추가했습니다");
    };
    reader.readAsDataURL(file);
    event.target.value = "";
  }

  function updateNode(id: string, patch: Partial<CanvasNode>) {
    const next = nodesRef.current.map((node) => node.id === id && !node.locked ? { ...node, ...patch } : node);
    nodesRef.current = next;
    setNodes(next);
  }

  const selectedNode = nodes.find((node) => node.id === selectedId);

  function deleteSelected() {
    if (!selectedId) return;
    commitNodes(nodesRef.current.filter((node) => node.id !== selectedId));
    setSelectedId(null);
  }

  function duplicateSelected() {
    const source = nodesRef.current.find((node) => node.id === selectedId);
    if (!source) return;
    commitNodes([...nodesRef.current, { ...source, id: makeId("copy"), name: `${source.name} copy`, x: (source.x || 0) + 24, y: (source.y || 0) + 24, locked: false }]);
  }

  function createCustomTheme() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const preview = canvas.toDataURL("image/png");
    const item: UserCustomTheme = { id: makeId("custom"), name: customName || "My Custom World", baseTheme, preview, createdAt: new Date().toISOString(), status: "draft" };
    const next = [item, ...customThemes].slice(0, 12);
    setCustomThemes(next);
    window.localStorage.setItem(CUSTOM_REGISTRY_KEY, JSON.stringify(next));
    onUseTheme(preview, item.name);
    onToast("User Custom UI를 미리보기에 적용했습니다");
  }

  const tools: { id: Tool; label: string }[] = [
    { id: "select", label: "선택" }, { id: "pen", label: "펜" }, { id: "brush", label: "브러시" }, { id: "eraser", label: "지우개" },
    { id: "line", label: "직선" }, { id: "rectangle", label: "사각형" }, { id: "circle", label: "원" }, { id: "triangle", label: "삼각형" },
    { id: "text", label: "텍스트" }, { id: "fill", label: "채우기" }, { id: "gradient", label: "그라디언트" },
  ];

  return <div className={`canvas-editor preview-${previewMode}`}>
    <div className="canvas-editor-header"><div><small>USER CUSTOM UI</small><h3>Canvas Editor</h3><p>직접 그리고, 배치하고, 저장할 수 있는 User Custom 작업 공간입니다.</p></div><div className="canvas-mode-row">{(["desktop", "mobile", "full"] as const).map((mode) => <button key={mode} type="button" className={previewMode === mode ? "is-selected" : ""} onClick={() => setPreviewMode(mode)}>{mode === "desktop" ? "Desktop" : mode === "mobile" ? "Mobile" : "Full screen"}</button>)}</div></div>
    <div className="canvas-toolbar"><div className="canvas-tool-row">{tools.map((item) => <button key={item.id} type="button" className={tool === item.id ? "is-selected" : ""} onClick={() => setTool(item.id)}>{item.label}</button>)}</div><div className="canvas-value-row"><label>색상 <input type="color" value={color} onChange={(event) => setColor(event.target.value)} /></label><label>크기 <input type="range" min="1" max="60" value={size} onChange={(event) => setSize(Number(event.target.value))} /><output>{size}</output></label><label>투명도 <input type="range" min="0.1" max="1" step="0.05" value={opacity} onChange={(event) => setOpacity(Number(event.target.value))} /><output>{Math.round(opacity * 100)}%</output></label><button type="button" onClick={undo} disabled={!history.length}>되돌리기</button><button type="button" onClick={redo} disabled={!redoStack.length}>다시 실행</button><button type="button" onClick={clearCanvas} disabled={!nodes.length}>전체 지우기</button></div><div className="canvas-option-row"><label>배경 <input type="color" value={background.startsWith("#") ? background : "#061011"} onChange={(event) => setBackground(event.target.value)} /></label><button type="button" className={grid ? "is-selected" : ""} onClick={() => setGrid((current) => !current)}>Grid</button><button type="button" className={snap ? "is-selected" : ""} onClick={() => setSnap((current) => !current)}>Snap</button><button type="button" className={safeArea ? "is-selected" : ""} onClick={() => setSafeArea((current) => !current)}>Safe Area</button><label className="zoom-control">Zoom <input type="range" min="0.5" max="1.4" step="0.1" value={zoom} onChange={(event) => setZoom(Number(event.target.value))} /><output>{Math.round(zoom * 100)}%</output></label></div></div>
    <div className="canvas-workspace"><div className="canvas-stage"><canvas ref={canvasRef} width={CANVAS_WIDTH} height={CANVAS_HEIGHT} style={{ transform: `scale(${zoom})` }} onPointerDown={handlePointerDown} onPointerMove={handlePointerMove} onPointerUp={(event) => { dragNodeRef.current = null; finishStroke(event); }} onPointerCancel={() => { activeRef.current = null; dragNodeRef.current = null; }} aria-label="User Custom Canvas" /></div><aside className="canvas-side-panel"><section><div className="canvas-section-heading"><strong>Assets</strong><label className="canvas-import"><input type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" onChange={importAsset} /><span>이미지 가져오기</span></label></div><input className="canvas-text-input" value={assetName} onChange={(event) => setAssetName(event.target.value)} aria-label="Asset name" /></section><section><div className="canvas-section-heading"><strong>Components</strong><span>Drag / place</span></div><div className="canvas-component-list">{["Ultra Brain", "OS Ecosystem", "UI Studio", "Workspace", "Project", "Search", "Settings"].map((component) => <button type="button" key={component} onClick={() => addComponent(component)}>{component}</button>)}</div></section><section><div className="canvas-section-heading"><strong>Layers</strong><span>{nodes.length}</span></div><div className="canvas-layer-list">{nodes.slice().reverse().map((node) => <div key={node.id} className={`canvas-layer ${selectedId === node.id ? "is-selected" : ""}`}><button type="button" onClick={() => setSelectedId(node.id)}>{node.name}</button><button type="button" onClick={() => updateNode(node.id, { visible: !node.visible })}>{node.visible ? "표시" : "숨김"}</button><button type="button" onClick={() => updateNode(node.id, { locked: !node.locked })}>{node.locked ? "잠금" : "해제"}</button></div>)}</div><div className="canvas-layer-actions"><button type="button" onClick={() => moveSelected(1)} disabled={!selectedId}>뒤로</button><button type="button" onClick={() => moveSelected(-1)} disabled={!selectedId}>앞으로</button><button type="button" onClick={duplicateSelected} disabled={!selectedId}>복제</button><button type="button" onClick={deleteSelected} disabled={!selectedId}>삭제</button></div></section><section><strong>User Custom Theme</strong><input className="canvas-text-input" value={customName} onChange={(event) => setCustomName(event.target.value)} aria-label="User Custom theme name" /><button className="canvas-primary-action" type="button" onClick={createCustomTheme}>User Custom UI 저장</button><div className="custom-theme-list">{customThemes.map((item) => <button type="button" key={item.id} onClick={() => onUseTheme(item.preview, item.name)}><img src={item.preview} alt="" /><span>{item.name}</span><small>{item.baseTheme}</small></button>)}</div></section></aside></div>
    {selectedNode && <div className="canvas-inspector-inline"><strong>선택 요소 · {selectedNode.name}</strong><label>X <input type="range" min="0" max={CANVAS_WIDTH} value={Math.round(selectedNode.x || 0)} onChange={(event) => updateNode(selectedNode.id, { x: Number(event.target.value) })} /></label><label>Y <input type="range" min="0" max={CANVAS_HEIGHT} value={Math.round(selectedNode.y || 0)} onChange={(event) => updateNode(selectedNode.id, { y: Number(event.target.value) })} /></label><label>너비 <input type="range" min="40" max="1000" value={Math.round(selectedNode.width || 250)} onChange={(event) => updateNode(selectedNode.id, { width: Number(event.target.value) })} /></label><label>높이 <input type="range" min="30" max="700" value={Math.round(selectedNode.height || 72)} onChange={(event) => updateNode(selectedNode.id, { height: Number(event.target.value) })} /></label><label>회전 <input type="range" min="-180" max="180" value={Math.round(selectedNode.rotation || 0)} onChange={(event) => updateNode(selectedNode.id, { rotation: Number(event.target.value) })} /></label><label>투명도 <input type="range" min="0.1" max="1" step="0.05" value={selectedNode.opacity} onChange={(event) => updateNode(selectedNode.id, { opacity: Number(event.target.value) })} /></label></div>}
  </div>;
}
