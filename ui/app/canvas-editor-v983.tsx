"use client";

import type { ChangeEvent, PointerEvent as ReactPointerEvent } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const CANVAS_WIDTH = 1200;
const CANVAS_HEIGHT = 760;
const STORAGE_KEY = "ultra-brain.user-custom/v3";

type UiTool = "select" | "button" | "text" | "card" | "panel" | "image" | "icon";
type DrawTool = "pen" | "pencil" | "brush" | "marker" | "airbrush" | "charcoal" | "watercolor" | "ink" | "chalk" | "spray" | "eraser" | "line" | "curve" | "rectangle" | "circle" | "triangle" | "text" | "fill" | "pan";
type CanvasPoint = { x: number; y: number; pressure: number; tiltX: number; tiltY: number; twist: number; time: number };
type ImageFilters = { brightness: number; contrast: number; saturation: number; hue: number; blur: number };
type Crop = { left: number; top: number; right: number; bottom: number };
type CanvasNode = {
  id: string;
  name: string;
  kind: "component" | "text" | "image" | "stroke" | "shape";
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  color: string;
  size: number;
  opacity: number;
  visible: boolean;
  locked: boolean;
  group?: string;
  points?: CanvasPoint[];
  start?: CanvasPoint;
  end?: CanvasPoint;
  tool?: DrawTool;
  text?: string;
  src?: string;
  target?: "ultra-brain" | "os-ecosystem";
  fill?: boolean;
  hardness?: number;
  flow?: number;
  spacing?: number;
  filters?: ImageFilters;
  crop?: Crop;
  mask?: "none" | "ellipse";
  shadow?: number;
  lighting?: number;
  texture?: number;
  blendMode?: GlobalCompositeOperation;
};
type Snapshot = { nodes: CanvasNode[]; background: string };
type Revision = Snapshot & { id: string; name: string; createdAt: string };
type Props = { baseTheme: string; onUseTheme: (preview: string, name: string) => void; onToast: (message: string) => void };

const PAINT_TOOLS: DrawTool[] = ["pen", "pencil", "brush", "marker", "airbrush", "charcoal", "watercolor", "ink", "chalk", "spray", "eraser"];
const UI_ACTIONS: Array<{ id: UiTool; label: string }> = [
  { id: "select", label: "선택·이동" },
  { id: "button", label: "버튼 추가" },
  { id: "text", label: "글자 추가" },
  { id: "card", label: "카드 추가" },
  { id: "panel", label: "패널 추가" },
];
const DRAW_TOOLS: Array<{ id: DrawTool; label: string }> = [
  { id: "pen", label: "펜" }, { id: "pencil", label: "연필" }, { id: "brush", label: "붓" },
  { id: "marker", label: "마커" }, { id: "airbrush", label: "에어브러시" }, { id: "charcoal", label: "목탄" },
  { id: "watercolor", label: "수채" }, { id: "ink", label: "잉크" }, { id: "chalk", label: "분필" },
  { id: "spray", label: "스프레이" }, { id: "eraser", label: "지우개" },
  { id: "line", label: "직선" }, { id: "curve", label: "곡선" }, { id: "rectangle", label: "사각형" },
  { id: "circle", label: "원" }, { id: "triangle", label: "삼각형" }, { id: "text", label: "글자" },
  { id: "fill", label: "영역 채우기" }, { id: "pan", label: "캔버스 이동" },
];
const DEFAULT_FILTERS: ImageFilters = { brightness: 1, contrast: 1, saturation: 1, hue: 0, blur: 0 };
const DEFAULT_CROP: Crop = { left: 0, top: 0, right: 0, bottom: 0 };

function makeId(prefix: string) { return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`; }
function cloneNodes(nodes: CanvasNode[]) {
  return nodes.map((node) => ({
    ...node,
    points: node.points?.map((point) => ({ ...point })),
    start: node.start ? { ...node.start } : undefined,
    end: node.end ? { ...node.end } : undefined,
    filters: node.filters ? { ...node.filters } : undefined,
    crop: node.crop ? { ...node.crop } : undefined,
  }));
}
function hexToRgb(hex: string) {
  const value = Number.parseInt(hex.replace("#", ""), 16);
  return { r: (value >> 16) & 255, g: (value >> 8) & 255, b: value & 255 };
}
function normalPressure(pointerType: string, value: number, enabled: boolean) {
  if (!enabled) return 1;
  if (pointerType === "pen") return Math.max(.08, value || .08);
  return .72;
}

export function CanvasEditorV983({ baseTheme, onUseTheme, onToast }: Props) {
  const contentRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<CanvasNode[]>([]);
  const backgroundRef = useRef("#061011");
  const imageCache = useRef(new Map<string, HTMLImageElement>());
  const activeRef = useRef<{ tool: DrawTool; start: CanvasPoint; points: CanvasPoint[]; pointerId: number } | null>(null);
  const dragRef = useRef<{ id: string; mode: "move" | "resize" | "rotate"; start: CanvasPoint; origin: { x: number; y: number; width: number; height: number; rotation: number }; before: Snapshot } | null>(null);
  const panRef = useRef<{ start: { x: number; y: number }; origin: { x: number; y: number }; pointerId: number } | null>(null);
  const penPointerRef = useRef<number | null>(null);
  const [nodes, setNodes] = useState<CanvasNode[]>([]);
  const [background, setBackgroundState] = useState("#061011");
  const [history, setHistory] = useState<Snapshot[]>([]);
  const [redoStack, setRedoStack] = useState<Snapshot[]>([]);
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [uiTool, setUiTool] = useState<UiTool | null>(null);
  const [drawTool, setDrawTool] = useState<DrawTool | null>(null);
  const [uiOpen, setUiOpen] = useState(true);
  const [drawingOpen, setDrawingOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [color, setColor] = useState("#c8a55d");
  const [size, setSize] = useState(10);
  const [opacity, setOpacity] = useState(1);
  const [flow, setFlow] = useState(.82);
  const [hardness, setHardness] = useState(.72);
  const [spacing, setSpacing] = useState(8);
  const [stabilizer, setStabilizer] = useState(.34);
  const [pressureEnabled, setPressureEnabled] = useState(true);
  const [shapeFill, setShapeFill] = useState(false);
  const [grid, setGrid] = useState(true);
  const [safeArea, setSafeArea] = useState(true);
  const [snap, setSnap] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [viewRotation, setViewRotation] = useState(0);
  const [viewOffset, setViewOffset] = useState({ x: 0, y: 0 });
  const [previewing, setPreviewing] = useState(false);
  const [draft, setDraft] = useState<CanvasNode | null>(null);
  const [inputDevice, setInputDevice] = useState("입력 장치 대기");
  const [textValue, setTextValue] = useState("");
  const [fontSize, setFontSize] = useState(32);
  const [customName, setCustomName] = useState(`${baseTheme} 사용자 UI`);
  const [revisionName, setRevisionName] = useState("UI 변경");
  const [navigationTarget, setNavigationTarget] = useState<"ultra-brain" | "os-ecosystem">("os-ecosystem");
  const [uiName, setUiName] = useState(`${baseTheme} 사용자 UI`);
  const [paintTick, setPaintTick] = useState(0);

  const selected = useMemo(() => nodes.filter((node) => selectedIds.includes(node.id)), [nodes, selectedIds]);
  const selectedOne = selected.length === 1 ? selected[0] : null;
  const selectedImage = selectedOne?.kind === "image" ? selectedOne : null;

  function setBackground(value: string) {
    backgroundRef.current = value;
    setBackgroundState(value);
  }

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      try {
        const saved = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "null");
        if (saved?.nodes && Array.isArray(saved.nodes)) { nodesRef.current = saved.nodes; setNodes(saved.nodes); }
        if (typeof saved?.background === "string") setBackground(saved.background);
        if (Array.isArray(saved?.revisions)) setRevisions(saved.revisions);
      } catch { /* local workspace is optional */ }
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  const snapshot = useCallback((): Snapshot => ({ nodes: cloneNodes(nodesRef.current), background: backgroundRef.current }), []);
  function restore(next: Snapshot) {
    const nextNodes = cloneNodes(next.nodes);
    nodesRef.current = nextNodes;
    setNodes(nextNodes);
    setBackground(next.background);
    setSelectedIds([]);
  }
  function commit(nextNodes: CanvasNode[], nextBackground = backgroundRef.current, message?: string) {
    setHistory((current) => [...current, snapshot()].slice(-60));
    setRedoStack([]);
    nodesRef.current = nextNodes;
    setNodes(nextNodes);
    setBackground(nextBackground);
    if (message) onToast(message);
  }
  function undo() {
    const previous = history.at(-1);
    if (!previous) return;
    setRedoStack((current) => [...current, snapshot()].slice(-60));
    setHistory((current) => current.slice(0, -1));
    restore(previous);
  }
  function redo() {
    const next = redoStack.at(-1);
    if (!next) return;
    setHistory((current) => [...current, snapshot()].slice(-60));
    setRedoStack((current) => current.slice(0, -1));
    restore(next);
  }

  function chooseUiTool(next: UiTool) {
    setDrawTool(null);
    setUiTool((current) => current === next ? null : next);
  }
  function chooseDrawTool(next: DrawTool) {
    setUiTool(null);
    setDrawTool((current) => current === next ? null : next);
  }

  function updateNode(id: string, patch: Partial<CanvasNode>, message?: string, allowLocked = false) {
    const next = nodesRef.current.map((node) => node.id === id && (allowLocked || !node.locked) ? { ...node, ...patch } : node);
    commit(next, backgroundRef.current, message);
  }
  function updateSelected(patch: Partial<CanvasNode>, message?: string) {
    if (!selectedIds.length) return;
    const next = nodesRef.current.map((node) => selectedIds.includes(node.id) && !node.locked ? { ...node, ...patch } : node);
    commit(next, backgroundRef.current, message);
  }
  function updateSelectedText(value: string) {
    setTextValue(value);
    if (selectedOne?.kind === "text") updateNode(selectedOne.id, { text: value, name: value || "글자" });
  }
  function newScreen() { commit([], "#061011", "새 화면을 만들었습니다"); setSelectedIds([]); }
  function duplicateSelected() {
    const copies = selected.filter((node) => !node.locked).map((node) => ({ ...node, id: makeId("copy"), name: `${node.name} 복사본`, x: node.x + 24, y: node.y + 24, locked: false }));
    if (!copies.length) return;
    commit([...nodesRef.current, ...cloneNodes(copies)], backgroundRef.current, "선택한 요소를 복제했습니다");
    setSelectedIds(copies.map((node) => node.id));
  }
  function deleteSelected() {
    const removable = new Set(selected.filter((node) => !node.locked).map((node) => node.id));
    if (!removable.size) return;
    commit(nodesRef.current.filter((node) => !removable.has(node.id)), backgroundRef.current, "선택한 요소를 삭제했습니다");
    setSelectedIds([]);
  }
  function reorderSelected(direction: 1 | -1) {
    if (!selectedIds.length) return;
    const next = [...nodesRef.current];
    const order = direction > 0 ? [...selectedIds].reverse() : selectedIds;
    order.forEach((id) => {
      const index = next.findIndex((node) => node.id === id);
      const target = Math.max(0, Math.min(next.length - 1, index + direction));
      if (index >= 0 && target !== index && !next[index].locked) { const [item] = next.splice(index, 1); next.splice(target, 0, item); }
    });
    commit(next, backgroundRef.current, direction > 0 ? "앞으로 옮겼습니다" : "뒤로 옮겼습니다");
  }
  function groupSelected() {
    if (selectedIds.length < 2) return;
    const group = makeId("group");
    updateSelected({ group }, "선택한 요소를 묶었습니다");
  }
  function alignSelected(axis: "x" | "y") {
    if (selected.length < 2) return;
    const anchor = selected[0];
    const next = nodesRef.current.map((node) => selectedIds.includes(node.id) && !node.locked ? { ...node, [axis]: axis === "x" ? anchor.x : anchor.y } : node);
    commit(next, backgroundRef.current, axis === "x" ? "가로 위치를 맞췄습니다" : "세로 위치를 맞췄습니다");
  }

  function addComponent(kind: Exclude<UiTool, "select" | "image">, point?: CanvasPoint) {
    const labels: Record<string, string> = { button: navigationTarget === "os-ecosystem" ? "OS Ecosystem" : "Ultra Brain", text: textValue || "글자", card: "카드", panel: "패널", icon: "아이콘" };
    const dimensions: Record<string, [number, number]> = { button: [250, 68], text: [300, 64], card: [340, 180], panel: [420, 240], icon: [76, 76] };
    const [width, height] = dimensions[kind] || [240, 66];
    const node: CanvasNode = {
      id: makeId(kind), name: labels[kind], kind: kind === "text" ? "text" : "component",
      text: kind === "text" ? textValue : labels[kind], target: kind === "button" ? navigationTarget : undefined,
      x: point?.x ?? 120 + (nodesRef.current.length % 3) * 280, y: point?.y ?? 100 + (nodesRef.current.length % 4) * 120,
      width, height, rotation: 0, color, size: fontSize, opacity, visible: true, locked: false,
    };
    commit([...nodesRef.current, node], backgroundRef.current, `${labels[kind]}을(를) 추가했습니다`);
    setSelectedIds([node.id]);
    setUiTool("select");
  }

  function importImage(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files || []);
    files.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = () => {
        const node: CanvasNode = {
          id: makeId("image"), name: file.name, kind: "image", src: String(reader.result),
          x: 70 + index * 28, y: 70 + index * 28, width: 600, height: 380, rotation: 0,
          color, size, opacity: 1, visible: true, locked: false,
          filters: { ...DEFAULT_FILTERS }, crop: { ...DEFAULT_CROP }, mask: "none", shadow: 0, lighting: 0, texture: 0, blendMode: "source-over",
        };
        commit([...nodesRef.current, node], backgroundRef.current, "그림을 가져왔습니다");
        setSelectedIds([node.id]);
      };
      reader.readAsDataURL(file);
    });
    event.target.value = "";
  }
  function importBackground(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => { commit(nodesRef.current, String(reader.result), "배경 이미지를 적용했습니다"); setSelectedIds([]); };
    reader.readAsDataURL(file);
    event.target.value = "";
  }

  const loadImage = useCallback((src: string) => {
    const cached = imageCache.current.get(src);
    if (cached) return cached;
    const image = new Image();
    image.onload = () => setPaintTick((value) => value + 1);
    image.src = src;
    imageCache.current.set(src, image);
    return image;
  }, []);

  const applyView = useCallback((context: CanvasRenderingContext2D) => {
    context.translate(CANVAS_WIDTH / 2 + viewOffset.x, CANVAS_HEIGHT / 2 + viewOffset.y);
    context.rotate((viewRotation * Math.PI) / 180);
    context.scale(zoom, zoom);
    context.translate(-CANVAS_WIDTH / 2, -CANVAS_HEIGHT / 2);
  }, [viewOffset, viewRotation, zoom]);

  const paintStroke = useCallback((context: CanvasRenderingContext2D, node: CanvasNode) => {
    const points = node.points || [];
    if (!points.length) return;
    context.save();
    context.globalCompositeOperation = node.tool === "eraser" ? "destination-out" : (node.blendMode || "source-over");
    context.strokeStyle = node.color;
    context.fillStyle = node.color;
    context.lineJoin = "round";
    context.lineCap = node.tool === "marker" ? "butt" : "round";
    const toolAlpha = node.tool === "pencil" ? .62 : node.tool === "marker" ? .38 : node.tool === "airbrush" ? .22 : node.tool === "watercolor" ? .34 : node.tool === "charcoal" ? .72 : node.tool === "chalk" ? .56 : node.tool === "spray" ? .24 : 1;
    if (node.tool === "airbrush") {
      const step = Math.max(1, Math.round((node.spacing || 8) / 3));
      points.forEach((point, index) => {
        if (index % step) return;
        const radius = Math.max(2, node.size * (.45 + point.pressure));
        const gradient = context.createRadialGradient(point.x, point.y, 0, point.x, point.y, radius);
        gradient.addColorStop(0, node.color);
        gradient.addColorStop(Math.max(.05, node.hardness || .5), `${node.color}66`);
        gradient.addColorStop(1, `${node.color}00`);
        context.globalAlpha = node.opacity * (node.flow || .8) * toolAlpha;
        context.fillStyle = gradient;
        context.beginPath(); context.arc(point.x, point.y, radius, 0, Math.PI * 2); context.fill();
      });
      context.restore();
      return;
    }
    for (let index = 1; index < points.length; index += 1) {
      const from = points[index - 1]; const to = points[index];
      const pressure = (from.pressure + to.pressure) / 2;
      const tilt = Math.min(1, Math.hypot(to.tiltX, to.tiltY) / 90);
      const scale = node.tool === "brush" ? .45 + pressure * 1.45 : node.tool === "marker" ? 2.1 : node.tool === "pencil" ? .35 + pressure * .5 : .25 + pressure * .9;
      context.lineWidth = Math.max(.6, node.size * scale * (1 + tilt * .15));
      context.globalAlpha = node.opacity * (node.flow || 1) * toolAlpha;
      context.beginPath(); context.moveTo(from.x, from.y); context.lineTo(to.x, to.y); context.stroke();
      if (node.tool === "pencil") {
        context.globalAlpha *= .22;
        context.beginPath(); context.moveTo(from.x + ((index % 3) - 1) * .8, from.y + .6); context.lineTo(to.x + .4, to.y - .5); context.stroke();
      }
    }
    context.restore();
  }, []);

  const paintNode = useCallback((context: CanvasRenderingContext2D, node: CanvasNode) => {
    if (!node.visible) return;
    context.save();
    context.globalAlpha = node.opacity;
    context.globalCompositeOperation = node.blendMode || "source-over";
    if (node.kind === "stroke") { paintStroke(context, node); context.restore(); return; }
    context.translate(node.x + node.width / 2, node.y + node.height / 2);
    context.rotate((node.rotation * Math.PI) / 180);
    context.translate(-(node.x + node.width / 2), -(node.y + node.height / 2));
    if (node.kind === "image" && node.src) {
      const image = loadImage(node.src);
      if (image.complete && image.naturalWidth) {
        const filters = node.filters || DEFAULT_FILTERS;
        context.filter = `brightness(${filters.brightness}) contrast(${filters.contrast}) saturate(${filters.saturation}) hue-rotate(${filters.hue}deg) blur(${filters.blur}px)`;
        if ((node.shadow || 0) > 0) { context.shadowColor = "rgba(0,0,0,.75)"; context.shadowBlur = node.shadow || 0; }
        if (node.mask === "ellipse") { context.beginPath(); context.ellipse(node.x + node.width / 2, node.y + node.height / 2, node.width / 2, node.height / 2, 0, 0, Math.PI * 2); context.clip(); }
        const crop = node.crop || DEFAULT_CROP;
        const sx = image.naturalWidth * crop.left; const sy = image.naturalHeight * crop.top;
        const sw = image.naturalWidth * Math.max(.05, 1 - crop.left - crop.right); const sh = image.naturalHeight * Math.max(.05, 1 - crop.top - crop.bottom);
        context.drawImage(image, sx, sy, sw, sh, node.x, node.y, node.width, node.height);
        context.filter = "none";
        if ((node.lighting || 0) > 0) { context.globalCompositeOperation = "screen"; context.fillStyle = `rgba(255,239,191,${Math.min(.45, node.lighting || 0)})`; context.fillRect(node.x, node.y, node.width, node.height); }
        if ((node.texture || 0) > 0) { context.globalCompositeOperation = "overlay"; context.globalAlpha = Math.min(.32, node.texture || 0); context.fillStyle = "rgba(255,255,255,.5)"; for (let y = node.y; y < node.y + node.height; y += 8) for (let x = node.x + (y % 16); x < node.x + node.width; x += 16) context.fillRect(x, y, 1, 1); }
      }
    } else if (node.kind === "shape" && node.start && node.end) {
      const x = Math.min(node.start.x, node.end.x); const y = Math.min(node.start.y, node.end.y);
      const width = Math.abs(node.end.x - node.start.x); const height = Math.abs(node.end.y - node.start.y);
      context.strokeStyle = node.color; context.fillStyle = node.color; context.lineWidth = node.size; context.lineCap = "round"; context.lineJoin = "round";
      context.beginPath();
      if (node.tool === "line") { context.moveTo(node.start.x, node.start.y); context.lineTo(node.end.x, node.end.y); }
      else if (node.tool === "curve") { context.moveTo(node.start.x, node.start.y); context.quadraticCurveTo((node.start.x + node.end.x) / 2, y - Math.max(30, height / 2), node.end.x, node.end.y); }
      else if (node.tool === "circle") context.ellipse(x + width / 2, y + height / 2, Math.max(1, width / 2), Math.max(1, height / 2), 0, 0, Math.PI * 2);
      else if (node.tool === "triangle") { context.moveTo(x + width / 2, y); context.lineTo(x + width, y + height); context.lineTo(x, y + height); context.closePath(); }
      else context.rect(x, y, width, height);
      if (node.fill) context.fill();
      context.stroke();
    } else if (node.kind === "text") {
      context.fillStyle = node.color; context.font = `600 ${Math.max(12, node.size)}px Pretendard, sans-serif`; context.textBaseline = "middle"; context.fillText(node.text || "글자", node.x + 12, node.y + node.height / 2);
    } else {
      context.fillStyle = `${node.color}24`; context.strokeStyle = node.color; context.lineWidth = 2;
      context.beginPath(); context.roundRect(node.x, node.y, node.width, node.height, node.kind === "component" ? 12 : 2); context.fill(); context.stroke();
      context.fillStyle = node.color; context.font = `600 ${Math.max(13, Math.min(22, node.size * .55))}px Pretendard, sans-serif`; context.textBaseline = "middle"; context.fillText(node.text || node.name, node.x + 18, node.y + node.height / 2);
    }
    context.restore();
  }, [loadImage, paintStroke]);

  const renderContent = useCallback((canvas: HTMLCanvasElement, nextNodes: CanvasNode[], nextBackground: string, nextDraft: CanvasNode | null, useView: boolean) => {
    const context = canvas.getContext("2d");
    if (!context) return;
    context.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    context.save();
    if (useView) applyView(context);
    if (nextBackground.startsWith("data:image/")) {
      const image = loadImage(nextBackground);
      if (image.complete && image.naturalWidth) context.drawImage(image, 0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
      else { context.fillStyle = "#061011"; context.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT); }
    } else { context.fillStyle = nextBackground; context.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT); }
    const layer = document.createElement("canvas"); layer.width = CANVAS_WIDTH; layer.height = CANVAS_HEIGHT;
    const layerContext = layer.getContext("2d");
    if (layerContext) {
      [...nextNodes, ...(nextDraft ? [nextDraft] : [])].forEach((node) => paintNode(layerContext, node));
      context.drawImage(layer, 0, 0);
    }
    context.restore();
  }, [applyView, loadImage, paintNode]);

  const renderOverlay = useCallback(() => {
    const canvas = overlayRef.current; const context = canvas?.getContext("2d");
    if (!canvas || !context) return;
    context.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    if (previewing) return;
    context.save(); applyView(context);
    if (grid) {
      context.strokeStyle = "rgba(200,165,93,.16)"; context.lineWidth = 1 / zoom;
      for (let x = 0; x <= CANVAS_WIDTH; x += 40) { context.beginPath(); context.moveTo(x, 0); context.lineTo(x, CANVAS_HEIGHT); context.stroke(); }
      for (let y = 0; y <= CANVAS_HEIGHT; y += 40) { context.beginPath(); context.moveTo(0, y); context.lineTo(CANVAS_WIDTH, y); context.stroke(); }
    }
    if (safeArea) { context.setLineDash([10 / zoom, 8 / zoom]); context.strokeStyle = "rgba(240,213,138,.65)"; context.lineWidth = 1 / zoom; context.strokeRect(56, 52, CANVAS_WIDTH - 112, CANVAS_HEIGHT - 104); context.setLineDash([]); }
    selected.forEach((node) => {
      context.save(); context.translate(node.x + node.width / 2, node.y + node.height / 2); context.rotate((node.rotation * Math.PI) / 180); context.translate(-(node.x + node.width / 2), -(node.y + node.height / 2));
      context.strokeStyle = node.locked ? "#d98d78" : "#f0d58a"; context.lineWidth = 2 / zoom; context.setLineDash([7 / zoom, 5 / zoom]); context.strokeRect(node.x - 7, node.y - 7, node.width + 14, node.height + 14); context.setLineDash([]); context.restore();
      if (!node.locked) {
        context.fillStyle = "#f0d58a";
        context.strokeStyle = "#111";
        context.lineWidth = 1 / zoom;
        const handles = [[node.x + node.width, node.y + node.height], [node.x + node.width, node.y - 34]];
        handles.forEach(([x, y]) => { context.beginPath(); context.arc(x, y, 7 / zoom, 0, Math.PI * 2); context.fill(); context.stroke(); });
        context.beginPath(); context.moveTo(node.x + node.width, node.y - 7); context.lineTo(node.x + node.width, node.y - 28); context.stroke();
      }
    });
    context.restore();
  }, [applyView, grid, previewing, safeArea, selected, zoom]);

  useEffect(() => {
    if (contentRef.current) renderContent(contentRef.current, nodes, background, draft, true);
    renderOverlay();
  }, [nodes, background, draft, paintTick, renderContent, renderOverlay]);

  function rawPoint(event: ReactPointerEvent<HTMLCanvasElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    return { x: ((event.clientX - rect.left) / rect.width) * CANVAS_WIDTH, y: ((event.clientY - rect.top) / rect.height) * CANVAS_HEIGHT };
  }
  function viewToCanvas(raw: { x: number; y: number }) {
    const dx = (raw.x - CANVAS_WIDTH / 2 - viewOffset.x) / zoom;
    const dy = (raw.y - CANVAS_HEIGHT / 2 - viewOffset.y) / zoom;
    const angle = (-viewRotation * Math.PI) / 180;
    return { x: dx * Math.cos(angle) - dy * Math.sin(angle) + CANVAS_WIDTH / 2, y: dx * Math.sin(angle) + dy * Math.cos(angle) + CANVAS_HEIGHT / 2 };
  }
  function eventPoint(event: ReactPointerEvent<HTMLCanvasElement>, nativeEvent: PointerEvent = event.nativeEvent): CanvasPoint {
    const rect = event.currentTarget.getBoundingClientRect();
    const raw = { x: ((nativeEvent.clientX - rect.left) / rect.width) * CANVAS_WIDTH, y: ((nativeEvent.clientY - rect.top) / rect.height) * CANVAS_HEIGHT };
    const point = viewToCanvas(raw);
    return {
      x: Math.max(-200, Math.min(CANVAS_WIDTH + 200, snap ? Math.round(point.x / 10) * 10 : point.x)),
      y: Math.max(-200, Math.min(CANVAS_HEIGHT + 200, snap ? Math.round(point.y / 10) * 10 : point.y)),
      pressure: normalPressure(nativeEvent.pointerType, nativeEvent.pressure, pressureEnabled),
      tiltX: nativeEvent.tiltX || 0, tiltY: nativeEvent.tiltY || 0, twist: nativeEvent.twist || 0, time: nativeEvent.timeStamp,
    };
  }
  function nodeBounds(node: CanvasNode) {
    if (node.kind === "stroke" && node.points?.length) {
      const xs = node.points.map((point) => point.x); const ys = node.points.map((point) => point.y);
      return { x: Math.min(...xs) - node.size, y: Math.min(...ys) - node.size, width: Math.max(24, Math.max(...xs) - Math.min(...xs) + node.size * 2), height: Math.max(24, Math.max(...ys) - Math.min(...ys) + node.size * 2) };
    }
    return { x: node.x, y: node.y, width: node.width, height: node.height };
  }
  function hitNode(point: CanvasPoint) {
    return [...nodesRef.current].reverse().find((node) => { const bounds = nodeBounds(node); return node.visible && point.x >= bounds.x - 16 && point.x <= bounds.x + bounds.width + 16 && point.y >= bounds.y - 16 && point.y <= bounds.y + bounds.height + 16; });
  }
  function transformHandle(point: CanvasPoint, node: CanvasNode): "resize" | "rotate" | null {
    const bounds = nodeBounds(node);
    const resizeDistance = Math.hypot(point.x - (bounds.x + bounds.width), point.y - (bounds.y + bounds.height));
    const rotateDistance = Math.hypot(point.x - (bounds.x + bounds.width), point.y - (bounds.y - 34));
    if (resizeDistance < 24) return "resize";
    if (rotateDistance < 24) return "rotate";
    return null;
  }
  function makeDraft(tool: DrawTool, start: CanvasPoint, end: CanvasPoint, points: CanvasPoint[]): CanvasNode {
    const x = Math.min(start.x, end.x); const y = Math.min(start.y, end.y); const width = Math.max(1, Math.abs(end.x - start.x)); const height = Math.max(1, Math.abs(end.y - start.y));
    return {
      id: "draft", name: "그리는 중", kind: PAINT_TOOLS.includes(tool) ? "stroke" : "shape", tool, points, start, end,
      x, y, width, height, rotation: 0, color, size, opacity, visible: true, locked: false, fill: shapeFill, hardness, flow, spacing,
    };
  }

  function handlePointerDown(event: ReactPointerEvent<HTMLCanvasElement>) {
    if (previewing) return;
    if (event.pointerType === "touch" && penPointerRef.current !== null) return;
    if (event.pointerType === "pen") penPointerRef.current = event.pointerId;
    event.currentTarget.setPointerCapture(event.pointerId);
    setInputDevice(event.pointerType === "pen" ? `터치펜 입력 · 압력 ${Math.round(event.pressure * 100)}%` : event.pointerType === "touch" ? "터치 입력" : "마우스 입력");
    const point = eventPoint(event);
    if (uiTool) {
      if (uiTool === "select") {
        const hit = hitNode(point); const additive = event.shiftKey || event.ctrlKey || event.metaKey;
        if (!hit) { if (!additive) setSelectedIds([]); return; }
        const selectedHandle = selectedOne?.id === hit.id ? transformHandle(point, hit) : null;
        setSelectedIds((current) => additive ? (current.includes(hit.id) ? current.filter((id) => id !== hit.id) : [...current, hit.id]) : [hit.id]);
        if (!hit.locked) dragRef.current = { id: hit.id, mode: selectedHandle || "move", start: point, origin: { x: hit.x, y: hit.y, width: hit.width, height: hit.height, rotation: hit.rotation }, before: snapshot() };
        return;
      }
      if (uiTool === "image") return;
      addComponent(uiTool, point);
      return;
    }
    if (!drawTool) return;
    if (drawTool === "pan") { panRef.current = { start: rawPoint(event), origin: viewOffset, pointerId: event.pointerId }; return; }
    if (drawTool === "fill") { floodFill(point); return; }
    if (drawTool === "text") { addComponent("text", point); return; }
    activeRef.current = { tool: drawTool, start: point, points: [point], pointerId: event.pointerId };
  }

  function handlePointerMove(event: ReactPointerEvent<HTMLCanvasElement>) {
    if (event.pointerType === "touch" && penPointerRef.current !== null) return;
    if (panRef.current?.pointerId === event.pointerId) {
      const raw = rawPoint(event); setViewOffset({ x: panRef.current.origin.x + raw.x - panRef.current.start.x, y: panRef.current.origin.y + raw.y - panRef.current.start.y }); return;
    }
    const point = eventPoint(event);
    if (dragRef.current) {
      const drag = dragRef.current; const dx = point.x - drag.start.x; const dy = point.y - drag.start.y;
      const next = nodesRef.current.map((node) => {
        if (node.id !== drag.id || node.locked) return node;
        if (drag.mode === "resize") return { ...node, width: Math.max(24, drag.origin.width + dx), height: Math.max(24, drag.origin.height + dy) };
        if (drag.mode === "rotate") {
          const center = { x: drag.origin.x + drag.origin.width / 2, y: drag.origin.y + drag.origin.height / 2 };
          const startAngle = Math.atan2(drag.start.y - center.y, drag.start.x - center.x);
          const nextAngle = Math.atan2(point.y - center.y, point.x - center.x);
          return { ...node, rotation: Math.round(drag.origin.rotation + ((nextAngle - startAngle) * 180) / Math.PI) };
        }
        return { ...node, x: drag.origin.x + dx, y: drag.origin.y + dy };
      });
      nodesRef.current = next; setNodes(next); return;
    }
    const active = activeRef.current;
    if (!active || active.pointerId !== event.pointerId) return;
    const coalesced = typeof event.nativeEvent.getCoalescedEvents === "function" ? event.nativeEvent.getCoalescedEvents() : [event.nativeEvent];
    coalesced.forEach((nativeEvent) => {
      const next = eventPoint(event, nativeEvent); const previous = active.points.at(-1) || next;
      active.points.push({ ...next, x: previous.x + (next.x - previous.x) * (1 - stabilizer), y: previous.y + (next.y - previous.y) * (1 - stabilizer) });
    });
    setDraft(makeDraft(active.tool, active.start, point, [...active.points]));
  }

  function finishPointer(event: ReactPointerEvent<HTMLCanvasElement>) {
    if (panRef.current?.pointerId === event.pointerId) { panRef.current = null; return; }
    if (dragRef.current) { const before = dragRef.current.before; dragRef.current = null; setHistory((current) => [...current, before].slice(-60)); setRedoStack([]); return; }
    const active = activeRef.current;
    if (!active || active.pointerId !== event.pointerId) return;
    const end = eventPoint(event); const node = makeDraft(active.tool, active.start, end, [...active.points, end]);
    node.id = makeId(active.tool); node.name = DRAW_TOOLS.find((item) => item.id === active.tool)?.label || "그림";
    activeRef.current = null; setDraft(null); commit([...nodesRef.current, node], backgroundRef.current, "그림 레이어를 추가했습니다"); setSelectedIds([node.id]);
    if (event.pointerType === "pen") penPointerRef.current = null;
  }
  function cancelPointer(event: ReactPointerEvent<HTMLCanvasElement>) {
    activeRef.current = null; dragRef.current = null; panRef.current = null; setDraft(null);
    if (event.pointerType === "pen") penPointerRef.current = null;
  }

  function floodFill(point: CanvasPoint) {
    const source = document.createElement("canvas"); source.width = CANVAS_WIDTH; source.height = CANVAS_HEIGHT;
    renderContent(source, nodesRef.current, backgroundRef.current, null, false);
    const sourceContext = source.getContext("2d", { willReadFrequently: true });
    if (!sourceContext) return;
    const image = sourceContext.getImageData(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT); const data = image.data;
    const startX = Math.max(0, Math.min(CANVAS_WIDTH - 1, Math.round(point.x))); const startY = Math.max(0, Math.min(CANVAS_HEIGHT - 1, Math.round(point.y)));
    const startIndex = (startY * CANVAS_WIDTH + startX) * 4; const target = [data[startIndex], data[startIndex + 1], data[startIndex + 2], data[startIndex + 3]];
    const replacement = hexToRgb(color); const output = new ImageData(CANVAS_WIDTH, CANVAS_HEIGHT); const seen = new Uint8Array(CANVAS_WIDTH * CANVAS_HEIGHT); const stack = [startY * CANVAS_WIDTH + startX]; const tolerance = 28;
    while (stack.length) {
      const pixel = stack.pop()!; if (seen[pixel]) continue; seen[pixel] = 1;
      const index = pixel * 4; const distance = Math.abs(data[index] - target[0]) + Math.abs(data[index + 1] - target[1]) + Math.abs(data[index + 2] - target[2]) + Math.abs(data[index + 3] - target[3]);
      if (distance > tolerance * 4) continue;
      output.data[index] = replacement.r; output.data[index + 1] = replacement.g; output.data[index + 2] = replacement.b; output.data[index + 3] = Math.round(opacity * 255);
      const x = pixel % CANVAS_WIDTH; const y = Math.floor(pixel / CANVAS_WIDTH);
      if (x > 0) stack.push(pixel - 1); if (x < CANVAS_WIDTH - 1) stack.push(pixel + 1); if (y > 0) stack.push(pixel - CANVAS_WIDTH); if (y < CANVAS_HEIGHT - 1) stack.push(pixel + CANVAS_WIDTH);
    }
    const mask = document.createElement("canvas"); mask.width = CANVAS_WIDTH; mask.height = CANVAS_HEIGHT; mask.getContext("2d")?.putImageData(output, 0, 0);
    const node: CanvasNode = { id: makeId("fill"), name: "채우기 레이어", kind: "image", src: mask.toDataURL("image/png"), x: 0, y: 0, width: CANVAS_WIDTH, height: CANVAS_HEIGHT, rotation: 0, color, size, opacity: 1, visible: true, locked: false, filters: { ...DEFAULT_FILTERS }, crop: { ...DEFAULT_CROP }, mask: "none", blendMode: "source-over" };
    commit([...nodesRef.current, node], backgroundRef.current, "연결된 영역을 채웠습니다"); setSelectedIds([node.id]);
  }

  function removeImageBackground() {
    if (!selectedImage?.src) return;
    const image = loadImage(selectedImage.src);
    if (!image.complete || !image.naturalWidth) { onToast("그림을 불러온 뒤 다시 눌러주세요"); return; }
    const canvas = document.createElement("canvas"); canvas.width = image.naturalWidth; canvas.height = image.naturalHeight;
    const context = canvas.getContext("2d", { willReadFrequently: true }); if (!context) return;
    context.drawImage(image, 0, 0); const pixels = context.getImageData(0, 0, canvas.width, canvas.height); const target = [pixels.data[0], pixels.data[1], pixels.data[2]];
    for (let index = 0; index < pixels.data.length; index += 4) {
      const distance = Math.hypot(pixels.data[index] - target[0], pixels.data[index + 1] - target[1], pixels.data[index + 2] - target[2]);
      if (distance < 52) pixels.data[index + 3] = Math.round(255 * Math.max(0, Math.min(1, (distance - 18) / 34)));
    }
    context.putImageData(pixels, 0, 0); updateNode(selectedImage.id, { src: canvas.toDataURL("image/png") }, "배경과 비슷한 색을 투명하게 만들었습니다");
  }

  function saveDraft() {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ nodes: nodesRef.current, background: backgroundRef.current, revisions }));
    onToast("이 기기에 작업을 저장했습니다");
  }
  function saveRevision() {
    const revision: Revision = { id: makeId("revision"), name: revisionName || "UI 변경", createdAt: new Date().toISOString(), ...snapshot() };
    const next = [revision, ...revisions].slice(0, 30); setRevisions(next);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ nodes: nodesRef.current, background: backgroundRef.current, revisions: next }));
    onToast("되돌릴 수 있는 변경 기록을 만들었습니다");
  }
  function rollback(revision: Revision) { setHistory((current) => [...current, snapshot()].slice(-60)); restore(revision); onToast(`${revision.name}(으)로 되돌렸습니다`); }
  function exportCanvas() {
    const canvas = document.createElement("canvas"); canvas.width = CANVAS_WIDTH; canvas.height = CANVAS_HEIGHT;
    renderContent(canvas, nodesRef.current, backgroundRef.current, null, false);
    return canvas;
  }
  function createCustomTheme() { const preview = exportCanvas().toDataURL("image/png"); const name = uiName.trim() || customName || `${baseTheme} 사용자 UI`; onUseTheme(preview, name); onToast("안내선 없이 사용자 UI를 저장했습니다"); }
  function downloadDrawing() {
    const link = document.createElement("a"); link.download = `${customName || "ultra-brain-ui"}.png`; link.href = exportCanvas().toDataURL("image/png"); link.click(); onToast("완성 이미지를 저장했습니다");
  }

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const command = event.ctrlKey || event.metaKey;
      if (command && event.key.toLowerCase() === "z") { event.preventDefault(); if (event.shiftKey) redo(); else undo(); }
      if (command && event.key.toLowerCase() === "y") { event.preventDefault(); redo(); }
      if ((event.key === "Delete" || event.key === "Backspace") && selectedIds.length && !(event.target instanceof HTMLInputElement)) { event.preventDefault(); deleteSelected(); }
      if (event.key === "Escape") { setUiTool(null); setDrawTool(null); setSelectedIds([]); }
    }
    window.addEventListener("keydown", onKeyDown); return () => window.removeEventListener("keydown", onKeyDown);
  });

  const updateSelectedFilter = (key: keyof ImageFilters, value: number) => {
    if (!selectedImage) return;
    updateNode(selectedImage.id, { filters: { ...(selectedImage.filters || DEFAULT_FILTERS), [key]: value } });
  };
  const updateCrop = (axis: "horizontal" | "vertical", value: number) => {
    if (!selectedImage) return;
    const amount = value / 200; const crop = selectedImage.crop || DEFAULT_CROP;
    updateNode(selectedImage.id, { crop: axis === "horizontal" ? { ...crop, left: amount, right: amount } : { ...crop, top: amount, bottom: amount } });
  };

  return <div className={`canvas-editor v983-canvas-editor ${previewing ? "is-previewing" : ""}`}>
    <header className="v983-editor-intro"><div><small>UI Studio · 사용자 지정 UI</small><h3>내 화면 만들기</h3><p>요소를 고른 뒤 캔버스에서 바로 움직이고 크기·회전을 조절하세요.</p></div><div className="v983-name-apply"><label>UI 이름<input value={uiName} onChange={(event) => setUiName(event.target.value)} aria-label="UI 이름" /></label><button type="button" className="v983-apply-button" aria-label="사용자 UI로 적용" onClick={() => { createCustomTheme(); onToast("만든 UI를 실제 화면에 적용했습니다"); }}>UI 적용</button><div className="v983-device-status"><span className="health-dot" />{inputDevice}</div></div></header>
    <div className="builder-workspace v983-workspace">
      <aside className="builder-tool-panel v983-tool-panels" aria-label="편집 도구함">
        <section className={`toolbox-section v983-toolbox ${uiOpen ? "is-open" : ""}`}>
          <button type="button" className="toolbox-heading" aria-expanded={uiOpen} aria-controls="v983-ui-tools" onClick={() => setUiOpen((value) => !value)}><strong><span aria-hidden="true">{uiOpen ? "▼" : "▶"}</span>UI/UX 도구함</strong><small>화면 요소·배치·저장</small></button>
          {uiOpen && <div className="toolbox-content" id="v983-ui-tools">
            <div className="v983-tool-group"><strong>화면</strong><div className="toolbox-chip-row"><button type="button" onClick={newScreen}>새 화면</button></div></div>
            <div className="v983-tool-group"><strong>요소 추가·선택</strong><div className="toolbox-chip-row">{UI_ACTIONS.map((item) => item.id === "image" ? null : <button key={item.id} type="button" aria-pressed={uiTool === item.id} className={uiTool === item.id ? "is-selected" : ""} onClick={() => chooseUiTool(item.id)}>{item.label}</button>)}</div><label>버튼 연결<select value={navigationTarget} onChange={(event) => setNavigationTarget(event.target.value as "ultra-brain" | "os-ecosystem")}><option value="ultra-brain">Ultra Brain</option><option value="os-ecosystem">OS Ecosystem</option></select></label><label>글자 내용<input value={selectedOne?.kind === "text" ? selectedOne.text || "" : textValue} onChange={(event) => updateSelectedText(event.target.value)} placeholder="여기에 글자를 입력하세요" /></label><label>글자 크기<input type="range" min="12" max="96" value={selectedOne?.kind === "text" ? selectedOne.size : fontSize} onChange={(event) => selectedOne?.kind === "text" ? updateNode(selectedOne.id, { size: Number(event.target.value) }) : setFontSize(Number(event.target.value))} /><output>{selectedOne?.kind === "text" ? selectedOne.size : fontSize}px</output></label></div>
            <div className="v983-tool-group"><strong>선택한 요소</strong><span>{selectedIds.length ? `${selectedIds.length}개 선택됨` : "캔버스에서 요소를 선택하세요"}</span><div className="toolbox-inline-actions"><button type="button" onClick={() => updateSelected({ width: Math.max(20, (selectedOne?.width || 240) - 20) })} disabled={!selectedIds.length}>너비 줄이기</button><button type="button" onClick={() => updateSelected({ width: (selectedOne?.width || 240) + 20 })} disabled={!selectedIds.length}>너비 늘리기</button><button type="button" onClick={() => updateSelected({ height: Math.max(20, (selectedOne?.height || 66) - 12) })} disabled={!selectedIds.length}>높이 줄이기</button><button type="button" onClick={() => updateSelected({ height: (selectedOne?.height || 66) + 12 })} disabled={!selectedIds.length}>높이 늘리기</button><button type="button" onClick={() => updateSelected({ rotation: (selectedOne?.rotation || 0) - 15 })} disabled={!selectedIds.length}>왼쪽 회전</button><button type="button" onClick={() => updateSelected({ rotation: (selectedOne?.rotation || 0) + 15 })} disabled={!selectedIds.length}>오른쪽 회전</button></div><label>투명도<input type="range" min=".1" max="1" step=".05" value={selectedOne?.opacity || 1} disabled={!selectedOne || selectedOne.locked} onChange={(event) => updateSelected({ opacity: Number(event.target.value) })} /><output>{Math.round((selectedOne?.opacity || 1) * 100)}%</output></label><div className="toolbox-inline-actions"><button type="button" onClick={() => alignSelected("x")} disabled={selectedIds.length < 2}>가로 맞춤</button><button type="button" onClick={() => alignSelected("y")} disabled={selectedIds.length < 2}>세로 맞춤</button><button type="button" onClick={groupSelected} disabled={selectedIds.length < 2}>묶기</button><button type="button" onClick={() => selectedOne && updateNode(selectedOne.id, { locked: !selectedOne.locked }, selectedOne.locked ? "잠금을 풀었습니다" : "요소를 잠갔습니다", true)} disabled={!selectedOne}>{selectedOne?.locked ? "잠금 풀기" : "잠그기"}</button></div></div>
            <div className="v983-tool-group"><strong>배치·레이어</strong><div className="toolbox-inline-actions"><button type="button" onClick={() => reorderSelected(1)} disabled={!selectedIds.length}>앞으로</button><button type="button" onClick={() => reorderSelected(-1)} disabled={!selectedIds.length}>뒤로</button><button type="button" className={grid ? "is-selected" : ""} aria-pressed={grid} onClick={() => setGrid((value) => !value)}>격자</button><button type="button" className={snap ? "is-selected" : ""} aria-pressed={snap} onClick={() => setSnap((value) => !value)}>딱 맞추기</button><button type="button" className={safeArea ? "is-selected" : ""} aria-pressed={safeArea} onClick={() => setSafeArea((value) => !value)}>안전 영역</button></div><div className="v983-layer-list">{nodes.slice().reverse().map((node) => <div key={node.id} className={selectedIds.includes(node.id) ? "is-selected" : ""}><button type="button" onClick={() => setSelectedIds([node.id])}>{node.name}</button><button type="button" onClick={() => updateNode(node.id, { visible: !node.visible }, node.visible ? "레이어를 숨겼습니다" : "레이어를 표시했습니다", true)} aria-label={`${node.name} ${node.visible ? "숨기기" : "표시"}`}>{node.visible ? "표시" : "숨김"}</button></div>)}</div></div>
          </div>}
        </section>

        <section className={`toolbox-section v983-toolbox ${drawingOpen ? "is-open" : ""}`}>
          <button type="button" className="toolbox-heading" aria-expanded={drawingOpen} aria-controls="v983-drawing-tools" onClick={() => setDrawingOpen((value) => !value)}><strong><span aria-hidden="true">{drawingOpen ? "▼" : "▶"}</span>그리기용 도구함</strong><small>그리기·이미지 편집·보정</small></button>
          {drawingOpen && <div className="toolbox-content" id="v983-drawing-tools">
            <div className="v983-tool-group"><strong>직접 그리기</strong><div className="toolbox-chip-row drawing-tools">{DRAW_TOOLS.filter((item) => PAINT_TOOLS.includes(item.id) || item.id === "fill" || item.id === "pan").map((item) => <button key={item.id} type="button" aria-pressed={drawTool === item.id} className={drawTool === item.id ? "is-selected" : ""} onClick={() => chooseDrawTool(item.id)}>{item.label}</button>)}</div></div>
            <div className="v983-tool-group"><strong>붓 설정</strong><label>색상<input type="color" value={color} onChange={(event) => setColor(event.target.value)} /></label><label>크기<input type="range" min="1" max="120" value={size} onChange={(event) => setSize(Number(event.target.value))} /><output>{size}px</output></label><label>투명도<input type="range" min=".05" max="1" step=".05" value={opacity} onChange={(event) => setOpacity(Number(event.target.value))} /><output>{Math.round(opacity * 100)}%</output></label><label>잉크 양<input type="range" min=".1" max="1" step=".05" value={flow} onChange={(event) => setFlow(Number(event.target.value))} /><output>{Math.round(flow * 100)}%</output></label><label>가장자리 선명도<input type="range" min=".05" max="1" step=".05" value={hardness} onChange={(event) => setHardness(Number(event.target.value))} /><output>{Math.round(hardness * 100)}%</output></label><label>분사 간격<input type="range" min="1" max="30" value={spacing} onChange={(event) => setSpacing(Number(event.target.value))} /><output>{spacing}</output></label><label>선 안정화<input type="range" min="0" max=".85" step=".05" value={stabilizer} onChange={(event) => setStabilizer(Number(event.target.value))} /><output>{Math.round(stabilizer * 100)}%</output></label><div className="toolbox-inline-actions"><button type="button" className={pressureEnabled ? "is-selected" : ""} aria-pressed={pressureEnabled} onClick={() => setPressureEnabled((value) => !value)}>펜 압력 {pressureEnabled ? "사용" : "끄기"}</button><button type="button" className={shapeFill ? "is-selected" : ""} aria-pressed={shapeFill} onClick={() => setShapeFill((value) => !value)}>도형 채우기 {shapeFill ? "사용" : "끄기"}</button></div></div>
            <div className="v983-tool-group"><strong>그림 편집·보정</strong>{selectedImage ? <><span>{selectedImage.name}</span><label>밝기<input type="range" min=".2" max="2" step=".05" value={(selectedImage.filters || DEFAULT_FILTERS).brightness} onChange={(event) => updateSelectedFilter("brightness", Number(event.target.value))} /></label><label>명암<input type="range" min=".2" max="2" step=".05" value={(selectedImage.filters || DEFAULT_FILTERS).contrast} onChange={(event) => updateSelectedFilter("contrast", Number(event.target.value))} /></label><label>채도<input type="range" min="0" max="2" step=".05" value={(selectedImage.filters || DEFAULT_FILTERS).saturation} onChange={(event) => updateSelectedFilter("saturation", Number(event.target.value))} /></label><label>색상<input type="range" min="-180" max="180" value={(selectedImage.filters || DEFAULT_FILTERS).hue} onChange={(event) => updateSelectedFilter("hue", Number(event.target.value))} /><output>{(selectedImage.filters || DEFAULT_FILTERS).hue}°</output></label><label>흐림<input type="range" min="0" max="20" value={(selectedImage.filters || DEFAULT_FILTERS).blur} onChange={(event) => updateSelectedFilter("blur", Number(event.target.value))} /><output>{(selectedImage.filters || DEFAULT_FILTERS).blur}px</output></label><label>가로 자르기<input type="range" min="0" max="80" value={Math.round(((selectedImage.crop?.left || 0) + (selectedImage.crop?.right || 0)) * 100)} onChange={(event) => updateCrop("horizontal", Number(event.target.value))} /></label><label>세로 자르기<input type="range" min="0" max="80" value={Math.round(((selectedImage.crop?.top || 0) + (selectedImage.crop?.bottom || 0)) * 100)} onChange={(event) => updateCrop("vertical", Number(event.target.value))} /></label><label>그림자<input type="range" min="0" max="50" value={selectedImage.shadow || 0} onChange={(event) => updateNode(selectedImage.id, { shadow: Number(event.target.value) })} /></label><label>광원<input type="range" min="0" max=".45" step=".05" value={selectedImage.lighting || 0} onChange={(event) => updateNode(selectedImage.id, { lighting: Number(event.target.value) })} /></label><label>질감<input type="range" min="0" max=".35" step=".05" value={selectedImage.texture || 0} onChange={(event) => updateNode(selectedImage.id, { texture: Number(event.target.value) })} /></label><label>합성 방식<select value={selectedImage.blendMode || "source-over"} onChange={(event) => updateNode(selectedImage.id, { blendMode: event.target.value as GlobalCompositeOperation })}><option value="source-over">일반</option><option value="multiply">곱하기</option><option value="screen">밝게 합치기</option><option value="overlay">겹쳐 합치기</option></select></label><div className="toolbox-inline-actions"><button type="button" onClick={removeImageBackground}>배경 제거</button><button type="button" className={selectedImage.mask === "ellipse" ? "is-selected" : ""} onClick={() => updateNode(selectedImage.id, { mask: selectedImage.mask === "ellipse" ? "none" : "ellipse" })}>원형 마스크</button><button type="button" onClick={() => commit(nodesRef.current, selectedImage.src || backgroundRef.current, "그림을 배경으로 사용합니다")}>배경으로 사용</button><button type="button" onClick={() => updateNode(selectedImage.id, { filters: { ...DEFAULT_FILTERS }, crop: { ...DEFAULT_CROP }, mask: "none", shadow: 0, lighting: 0, texture: 0, blendMode: "source-over" }, "그림 보정을 초기화했습니다")}>보정 초기화</button></div></> : <span>그림 레이어를 선택하면 자르기·색 보정·배경 제거·마스크·합성을 사용할 수 있습니다.</span>}</div>
            <div className="v983-tool-group"><strong>캔버스 보기</strong><div className="toolbox-inline-actions"><button type="button" onClick={() => setZoom((value) => Math.min(4, value * 1.2))}>확대</button><button type="button" onClick={() => setZoom((value) => Math.max(.25, value / 1.2))}>축소</button><button type="button" onClick={() => { setZoom(1); setViewOffset({ x: 0, y: 0 }); setViewRotation(0); }}>화면 맞춤</button><button type="button" onClick={() => setViewRotation((value) => value - 15)}>왼쪽 회전</button><button type="button" onClick={() => setViewRotation((value) => value + 15)}>오른쪽 회전</button><button type="button" onClick={() => { setViewOffset({ x: 0, y: 0 }); setViewRotation(0); }}>보기 초기화</button></div><span>확대 {Math.round(zoom * 100)}% · 회전 {viewRotation}°</span></div>
            <div className="v983-tool-group"><strong>그림 파일</strong><div className="toolbox-inline-actions"><button type="button" onClick={downloadDrawing}>PNG 저장</button></div></div>
          </div>}
        </section>
      </aside>

      <div className="builder-canvas-column v983-canvas-column">
        <div className="v983-shared-actions" aria-label="공용 작업 기능"><div className="v983-insert-tools"><label className="builder-file-action"><input type="file" accept="image/*" onChange={importBackground} /><span>배경 이미지</span></label><label className="builder-file-action"><input type="file" accept="image/*" onChange={importImage} /><span>이미지 삽입</span></label><button type="button" onClick={() => addComponent("icon")}>아이콘 삽입</button><button type="button" className={drawTool === "rectangle" ? "is-selected" : ""} onClick={() => chooseDrawTool("rectangle")}>도형</button><button type="button" className={drawTool === "line" ? "is-selected" : ""} onClick={() => chooseDrawTool("line")}>선</button></div><div className="v983-common-tools"><button type="button" onClick={undo} disabled={!history.length}>되돌리기</button><button type="button" onClick={redo} disabled={!redoStack.length}>다시 실행</button><button type="button" onClick={deleteSelected} disabled={!selectedIds.length}>삭제</button><button type="button" className={previewing ? "is-selected" : ""} onClick={() => setPreviewing((value) => !value)}>{previewing ? "편집으로 돌아가기" : "미리보기"}</button></div></div>
        <div className={`canvas-stage v983-canvas-stage ${drawTool === "pan" ? "is-panning" : ""}`}>
          <canvas ref={contentRef} width={CANVAS_WIDTH} height={CANVAS_HEIGHT} aria-hidden="true" />
          <canvas ref={overlayRef} width={CANVAS_WIDTH} height={CANVAS_HEIGHT} onPointerDown={handlePointerDown} onPointerMove={handlePointerMove} onPointerUp={finishPointer} onPointerCancel={cancelPointer} aria-label="사용자 UI 작업 캔버스" />
          {previewing && <div className="canvas-preview-badge">미리보기 · 안내선과 선택선은 저장되지 않습니다</div>}
          {!nodes.length && !draft && <div className="canvas-empty">도구를 골라 그리거나 화면 요소를 추가하세요</div>}
        </div>
      </div>
      <aside className="v983-properties-panel" aria-label="선택한 요소 속성"><section><div className="v983-panel-heading"><strong>속성</strong><span>{selectedOne ? "선택됨" : "선택 없음"}</span></div>{selectedOne ? <><label>이름<input value={selectedOne.name} onChange={(event) => updateNode(selectedOne.id, { name: event.target.value })} /></label>{selectedOne.kind === "text" && <label>글자<input value={selectedOne.text || ""} onChange={(event) => updateSelectedText(event.target.value)} /></label>}<div className="v983-property-grid"><label>가로 위치<input type="number" value={Math.round(selectedOne.x)} onChange={(event) => updateNode(selectedOne.id, { x: Number(event.target.value) })} /></label><label>세로 위치<input type="number" value={Math.round(selectedOne.y)} onChange={(event) => updateNode(selectedOne.id, { y: Number(event.target.value) })} /></label><label>너비<input type="number" min="24" value={Math.round(selectedOne.width)} onChange={(event) => updateNode(selectedOne.id, { width: Math.max(24, Number(event.target.value)) })} /></label><label>높이<input type="number" min="24" value={Math.round(selectedOne.height)} onChange={(event) => updateNode(selectedOne.id, { height: Math.max(24, Number(event.target.value)) })} /></label></div><label>회전<input type="range" min="-180" max="180" value={Math.round(selectedOne.rotation)} onChange={(event) => updateNode(selectedOne.id, { rotation: Number(event.target.value) })} /></label><label>색상<input type="color" value={selectedOne.color} onChange={(event) => updateSelected({ color: event.target.value })} /></label><label>투명도<input type="range" min=".05" max="1" step=".05" value={selectedOne.opacity} onChange={(event) => updateSelected({ opacity: Number(event.target.value) })} /></label><button type="button" className={selectedOne.locked ? "is-selected" : ""} onClick={() => updateNode(selectedOne.id, { locked: !selectedOne.locked }, undefined, true)}>{selectedOne.locked ? "잠금 풀기" : "잠그기"}</button></> : <p>캔버스에서 요소를 누르면 위치·크기·회전·색상을 조절할 수 있습니다.</p>}</section><section><div className="v983-panel-heading"><strong>레이어</strong><span>{nodes.length}개</span></div><div className="v983-layer-list">{nodes.slice().reverse().map((node) => <div key={node.id} className={selectedIds.includes(node.id) ? "is-selected" : ""}><button type="button" onClick={() => { setUiTool("select"); setDrawTool(null); setSelectedIds([node.id]); }}>{node.name || "이름 없는 요소"}</button><button type="button" onClick={() => updateNode(node.id, { visible: !node.visible }, undefined, true)} aria-label={`${node.name} ${node.visible ? "숨기기" : "표시"}`}>{node.visible ? "표시" : "숨김"}</button></div>)}</div></section></aside>
    </div>
  </div>;
}
