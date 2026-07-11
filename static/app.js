import React, { useEffect, useMemo, useRef, useState } from "https://esm.sh/react@18.3.1";
import { createRoot } from "https://esm.sh/react-dom@18.3.1/client";

const h = React.createElement;

const SAMPLE = `As AI tools become woven into everyday research and product work, teams are experiencing a significant transformation in how they draft, revise, and publish written material. This paper aims to explore the important value of AI-assisted writing and analyze its role in productivity, knowledge synthesis, and editorial decision-making.

First, AI systems can quickly organize scattered notes and help writers identify weak sections in an argument, thereby providing more precise guidance for revision. Second, automated drafting tools can improve the efficiency of repetitive writing tasks and reduce the burden of routine editing. Finally, these systems may also introduce concerns around accuracy, originality, privacy, and over-reliance on generic phrasing.

In conclusion, AI-assisted writing has important significance and broad prospects across academic and professional contexts. Organizations should establish a balanced process across tool use, editorial review, and ethical standards in order to improve writing quality in a sustainable way.`;

const DEFAULT_PIPELINE = [
  "blader_humanizer",
  "stephenturner_skill_deslop",
];
const HIDDEN_PROGRESS = { visible: false, phase: "idle", percent: 0 };

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function paragraphsOf(value) {
  return value.trim() ? value.trim().split(/\n\s*\n+/).length : 0;
}

function nodeCountLabel(count) {
  return `${count} ${count === 1 ? "node" : "nodes"}`;
}

function adapterKind(adapter) {
  if (!adapter) return "";
  if (adapter.kind === "command" || adapter.kind === "python_import") return "Local";
  if (adapter.kind === "analysis_then_llm") return "Analyze + LLM";
  return adapter.integration_mode === "native_skill" ? "Skill" : "LLM";
}

function Button({ children, className = "", disabled = false, ...props }) {
  return h(
    "button",
    { className: `button ${className}`.trim(), disabled, ...props },
    children,
  );
}

function Glyph({ children }) {
  return h("span", { className: "button-glyph", "aria-hidden": "true" }, children);
}

function Stat({ label, value }) {
  return h("div", { className: "stat" }, [
    h("span", { key: "label" }, label),
    h("strong", { key: "value" }, value),
  ]);
}

function StatusPill({ health, loading }) {
  const ok = Boolean(health?.ok && (health?.hasKey || health?.demoMode));
  const label = loading
    ? "Connecting"
    : health?.demoMode
      ? `${health.adapters} nodes demo mode`
      : ok
        ? `${health.adapters} nodes ready`
        : "API key required";
  return h("div", { className: `status-pill ${ok ? "ok" : "warn"}` }, label);
}

function ProgressOverlay({ progress, stepCount }) {
  if (!progress.visible) return null;
  const percent = Math.max(0, Math.min(100, progress.percent));
  const rounded = Math.round(percent);
  const status = progress.phase === "complete" ? "Finalizing" : progress.phase === "leaving" ? "Done" : "Running nodes";

  return h("div", { className: `progress-float ${progress.phase}`, role: "status", "aria-live": "polite" }, [
    h("div", { className: "progress-card", key: "card" }, [
      h("div", { className: "progress-ring-wrap", key: "ring" }, [
        h("div", {
          className: "progress-ring",
          style: { "--progress": percent },
          "aria-hidden": "true",
          key: "ring-value",
        }, [
          h("span", { className: "progress-hole", key: "hole" }),
          h("span", { className: "progress-spark", key: "spark" }),
        ]),
        h("div", { className: "progress-percent", key: "percent" }, `${rounded}%`),
      ]),
      h("div", { className: "progress-copy", key: "copy" }, [
        h("strong", { key: "status" }, status),
        h("span", { key: "detail" }, `${nodeCountLabel(stepCount)} in sequence`),
      ]),
    ]),
  ]);
}

function AdapterRow({ adapter, onAdd }) {
  return h("article", { className: "adapter-row" }, [
    h("div", { className: "adapter-main", key: "main" }, [
      h("div", { className: "adapter-title", key: "title" }, adapter.name),
      h("div", { className: "adapter-repo", key: "repo" }, adapter.repo),
      h("p", { className: "adapter-desc", key: "desc" }, adapter.description),
    ]),
    h("div", { className: "adapter-meta", key: "meta" }, [
      h("span", { className: "tag", key: "cat" }, adapter.category || "Other"),
      h("span", { className: "tag", key: "kind" }, adapterKind(adapter)),
      h("span", { className: "tag ok-tag", key: "state" }, adapter.source_cached ? "Source cached" : "Built-in"),
    ]),
    h(Button, { className: "compact add-node", onClick: () => onAdd(adapter.id), key: "button" }, [
      h(Glyph, { key: "icon" }, "+"),
      h("span", { key: "text" }, "Add"),
    ]),
  ]);
}

function PipelineRow({ adapter, index, total, onMove, onRemove, onDragStart, onDrop }) {
  return h(
    "article",
    {
      className: "pipeline-row",
      draggable: true,
      onDragStart: () => onDragStart(index),
      onDragOver: (event) => event.preventDefault(),
      onDrop: () => onDrop(index),
    },
    [
      h("div", { className: "order", key: "order" }, String(index + 1).padStart(2, "0")),
      h("div", { className: "pipeline-copy", key: "copy" }, [
        h("div", { className: "pipeline-name", key: "name" }, adapter?.name || "Unknown node"),
        h("div", { className: "pipeline-repo", key: "repo" }, adapter?.repo || ""),
      ]),
      h("div", { className: "pipeline-kind", key: "kind" }, adapterKind(adapter)),
      h("div", { className: "row-actions", key: "actions" }, [
        h(Button, { className: "icon", disabled: index === 0, onClick: () => onMove(index, -1), title: "Move up", "aria-label": "Move up", key: "up" }, "↑"),
        h(Button, { className: "icon", disabled: index === total - 1, onClick: () => onMove(index, 1), title: "Move down", "aria-label": "Move down", key: "down" }, "↓"),
        h(Button, { className: "icon danger", onClick: () => onRemove(index), title: "Remove", "aria-label": "Remove", key: "remove" }, "×"),
      ]),
    ],
  );
}

function App() {
  const [health, setHealth] = useState(null);
  const [adapters, setAdapters] = useState([]);
  const [pipeline, setPipeline] = useState(DEFAULT_PIPELINE);
  const [category, setCategory] = useState("All");
  const [query, setQuery] = useState("");
  const [input, setInput] = useState(SAMPLE);
  const [note, setNote] = useState("Preserve paragraph structure, keep citations and technical terms, and return only the rewritten prose.");
  const [output, setOutput] = useState("");
  const [steps, setSteps] = useState([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [dragIndex, setDragIndex] = useState(null);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(HIDDEN_PROGRESS);
  const progressFrameRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const [healthRes, adapterRes] = await Promise.all([
          fetch("/api/health"),
          fetch("/api/adapters"),
        ]);
        const healthData = await healthRes.json();
        const adapterData = await adapterRes.json();
        if (!mounted) return;
        setHealth(healthData);
        setAdapters(adapterData.adapters || []);
      } catch (err) {
        if (mounted) setError(err.message || "Backend connection failed");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (progressFrameRef.current) {
        cancelAnimationFrame(progressFrameRef.current);
      }
    };
  }, []);

  const adapterMap = useMemo(() => new Map(adapters.map((adapter) => [adapter.id, adapter])), [adapters]);
  const categories = useMemo(() => ["All", ...Array.from(new Set(adapters.map((adapter) => adapter.category || "Other"))).sort()], [adapters]);

  const visibleAdapters = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return adapters.filter((adapter) => {
      const categoryMatch = category === "All" || adapter.category === category;
      const queryMatch = !needle || [adapter.name, adapter.repo, adapter.description, adapter.category]
        .join(" ")
        .toLowerCase()
        .includes(needle);
      return categoryMatch && queryMatch;
    });
  }, [adapters, category, query]);

  const pipelineAdapters = pipeline.map((id) => adapterMap.get(id)).filter(Boolean);
  const cachedSourceCount = adapters.filter((adapter) => adapter.source_cached).length;

  function addNode(id) {
    setPipeline((current) => [...current, id]);
  }

  function removeNode(index) {
    setPipeline((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  function moveNode(index, direction) {
    setPipeline((current) => {
      const target = index + direction;
      if (target < 0 || target >= current.length) return current;
      const next = [...current];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  function dropNode(targetIndex) {
    if (dragIndex === null || dragIndex === targetIndex) return;
    setPipeline((current) => {
      const next = [...current];
      const [item] = next.splice(dragIndex, 1);
      next.splice(targetIndex, 0, item);
      return next;
    });
    setDragIndex(null);
  }

  function stopProgressLoop() {
    if (progressFrameRef.current) {
      cancelAnimationFrame(progressFrameRef.current);
      progressFrameRef.current = null;
    }
  }

  function startProgressLoop() {
    stopProgressLoop();
    const startedAt = performance.now();
    setProgress({ visible: true, phase: "running", percent: 2 });

    const tick = () => {
      const elapsed = performance.now() - startedAt;
      const easingTarget = Math.min(94, 7 + 88 * (1 - Math.exp(-elapsed / 7600)));
      const shimmer = Math.sin(elapsed / 240) * 0.32;
      setProgress((current) => {
        if (current.phase !== "running") return current;
        return {
          ...current,
          percent: Math.min(94, Math.max(current.percent + 0.06, easingTarget + shimmer)),
        };
      });
      progressFrameRef.current = requestAnimationFrame(tick);
    };

    progressFrameRef.current = requestAnimationFrame(tick);
  }

  async function completeProgressBeforeReveal() {
    stopProgressLoop();
    setProgress({ visible: true, phase: "complete", percent: 100 });
    await delay(460);
  }

  async function dismissProgress() {
    setProgress((current) => ({ ...current, visible: true, phase: "leaving", percent: 100 }));
    await delay(420);
    setProgress(HIDDEN_PROGRESS);
  }

  async function runPipeline() {
    if (running || !input.trim() || !pipeline.length) return;
    setRunning(true);
    setError("");
    setOutput("");
    setSteps([]);
    startProgressLoop();
    try {
      const response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: input, note, pipeline }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Run failed");
      await completeProgressBeforeReveal();
      setOutput(data.output || "");
      setSteps(data.steps || []);
      await dismissProgress();
    } catch (err) {
      stopProgressLoop();
      setError(err.message || "Run failed");
      await dismissProgress();
    } finally {
      setRunning(false);
    }
  }

  return h("div", { className: "app-shell" }, [
    h(ProgressOverlay, { progress, stepCount: pipeline.length, key: "progress" }),
    h("header", { className: "topbar", key: "topbar" }, [
      h("div", { className: "brand", key: "brand" }, [
        h("span", { className: "brand-mark", key: "mark" }, "D"),
        h("div", { key: "copy" }, [
          h("div", { className: "brand-name", key: "name" }, "De-AI"),
          h("div", { className: "brand-sub", key: "sub" }, "Humanizer pipeline"),
        ]),
      ]),
      h(StatusPill, { health, loading, key: "status" }),
    ]),

    h("main", { className: "main-grid", key: "main" }, [
      h("section", { className: "surface editor-surface", key: "editor" }, [
        h("div", { className: "surface-head", key: "head" }, [
          h("div", { key: "title" }, [
            h("h1", { key: "h1" }, "Rewrite Workbench"),
            h("p", { key: "p" }, "Paste, sequence, rewrite, inspect."),
          ]),
          h("div", { className: "stats", key: "stats" }, [
            h(Stat, { label: "Input", value: `${input.length} chars / ${paragraphsOf(input)} paras`, key: "in" }),
            h(Stat, { label: "Output", value: output ? `${output.length} chars / ${paragraphsOf(output)} paras` : "Ready", key: "out" }),
          ]),
        ]),
        h("div", { className: "workbench-grid", key: "grid" }, [
          h("div", { className: "text-column input-pane", key: "input" }, [
            h("div", { className: "field-head", key: "head" }, [
              h("label", { htmlFor: "inputText", key: "label" }, "Input"),
              h("div", { className: "inline-actions", key: "actions" }, [
                h(Button, { className: "compact", onClick: () => setInput(SAMPLE), key: "sample" }, "Sample"),
                h(Button, { className: "compact", onClick: () => setInput(""), key: "clear" }, "Clear"),
              ]),
            ]),
            h("textarea", {
              id: "inputText",
              value: input,
              onChange: (event) => setInput(event.target.value),
              spellCheck: false,
              key: "textarea",
            }),
            h("input", {
              className: "note-input",
              value: note,
              onChange: (event) => setNote(event.target.value),
              placeholder: "Run note",
              key: "note",
            }),
          ]),
          h("aside", { className: "pipeline-column", key: "pipeline" }, [
            h("div", { className: "pipeline-column-head", key: "head" }, [
              h("div", { key: "title" }, [
                h("h2", { key: "h2" }, "Pipeline"),
                h("p", { key: "p" }, `${nodeCountLabel(pipeline.length)}, top to bottom.`),
              ]),
              h(Button, { className: "compact ghost-on-dark", onClick: () => setPipeline(DEFAULT_PIPELINE), key: "reset" }, [
                h(Glyph, { key: "icon" }, "↺"),
                h("span", { key: "text" }, "Default"),
              ]),
            ]),
            h("div", { className: "pipeline-list vertical-pipeline", key: "list" },
              pipelineAdapters.length
                ? pipelineAdapters.map((adapter, index) => h(PipelineRow, {
                    adapter,
                    index,
                    total: pipelineAdapters.length,
                    onMove: moveNode,
                    onRemove: removeNode,
                    onDragStart: setDragIndex,
                    onDrop: dropNode,
                    key: `${adapter.id}-${index}`,
                  }))
                : h("div", { className: "empty-state" }, "Add nodes from the library"),
            ),
          ]),
          h("div", { className: "text-column output-pane", key: "output" }, [
            h("div", { className: "field-head", key: "head" }, [
              h("label", { htmlFor: "outputText", key: "label" }, "Output"),
              h(Button, { className: "primary", disabled: running || !input.trim() || !pipeline.length, onClick: runPipeline, key: "run" }, [
                h(Glyph, { key: "icon" }, running ? "…" : "▶"),
                h("span", { key: "text" }, running ? "Running" : "Run pipeline"),
              ]),
            ]),
            h("textarea", {
              id: "outputText",
              value: output,
              readOnly: true,
              spellCheck: false,
              placeholder: error || "Final rewritten prose appears here",
              key: "textarea",
            }),
            h("div", { className: error ? "run-summary error" : "run-summary", key: "summary" },
              error
                ? error
                : steps.length
                  ? `${steps.filter((step) => step.ok).length}/${steps.length} nodes completed, final ${output.length} chars.`
                  : "Waiting to run",
            ),
          ]),
        ]),
      ]),

      h("section", { className: "surface library-surface", key: "library" }, [
        h("div", { className: "surface-head compact-head", key: "head" }, [
          h("div", { key: "title" }, [
            h("h2", { key: "h2" }, "Node Library"),
            h("p", { key: "p" }, `${visibleAdapters.length}/${adapters.length} nodes, ${cachedSourceCount} source caches.`),
          ]),
          h("input", {
            className: "search-input",
            value: query,
            onChange: (event) => setQuery(event.target.value),
            placeholder: "Search nodes or repos",
            key: "search",
          }),
        ]),
        h("div", { className: "segments", key: "segments" }, categories.map((item) =>
          h("button", {
            className: item === category ? "segment active" : "segment",
            onClick: () => setCategory(item),
            key: item,
          }, item),
        )),
        h("div", { className: "adapter-list", key: "list" }, visibleAdapters.map((adapter) =>
          h(AdapterRow, { adapter, onAdd: addNode, key: adapter.id }),
        )),
      ]),
    ]),
  ]);
}

createRoot(document.getElementById("root")).render(h(App));
