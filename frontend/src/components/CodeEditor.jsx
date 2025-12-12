// src/components/CodeEditors.jsx
import { useRef, useState } from "react";
import Editor from "@monaco-editor/react";

export default function CodeEditors({ code, setCode, cpp }) {
  const pyEditorRef = useRef(null);
  const cppEditorRef = useRef(null);
  const [split, setSplit] = useState(50); // % ширины левой панели

  function handleMountPython(editor, monaco) {
    pyEditorRef.current = editor;

    // Тема
    monaco.editor.defineTheme("midnight", {
      base: "vs-dark",
      inherit: true,
      rules: [{ token: "", foreground: "E8ECF1" }],
      colors: {
        "editor.background": "#0c1420",
        "editor.selectionBackground": "#27406088",
        "editor.lineHighlightBackground": "#101a2a",
        "editorCursor.foreground": "#22d3ee",
        "editorIndentGuide.background": "#2b3a52",
        "editorIndentGuide.activeBackground": "#4d6ea4",
      },
    });
    monaco.editor.setTheme("midnight");

    // Конфиг Python: авто-отступ после ":" + автоскобки/кавычки
    monaco.languages.setLanguageConfiguration("python", {
      autoClosingPairs: [
        { open: "(", close: ")" },
        { open: "[", close: "]" },
        { open: "{", close: "}" },
        { open: "'", close: "'", notIn: ["string", "comment"] },
        { open: '"', close: '"', notIn: ["string", "comment"] },
      ],
      brackets: [
        ["{", "}"],
        ["[", "]"],
        ["(", ")"],
      ],
      indentationRules: {
        increaseIndentPattern: /:\s*($|#)/,
        decreaseIndentPattern: /^\s*(elif|else|except|finally)\b.*:\s*($|#)/,
      },
      onEnterRules: [
        {
          beforeText: /^.*:\s*($|#)/,
          action: { indentAction: monaco.languages.IndentAction.Indent },
        },
      ],
    });

    // Настройки редактора
    editor.updateOptions({
      wordWrap: "on",
      tabSize: 4,
      insertSpaces: true,
      autoClosingBrackets: "always",
      autoClosingQuotes: "always",
      autoIndent: "full",
      formatOnPaste: false,
      formatOnType: false,
      minimap: { enabled: false },
      smoothScrolling: true,
      scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 },
      scrollBeyondLastLine: false,
      renderLineHighlight: "line",
      renderWhitespace: "selection",
      bracketPairColorization: { enabled: true },
      guides: { indentation: true, bracketPairs: true },
    });

    // Ctrl/Cmd+S — заглушка, чтобы не открывалась системная приблуда
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {});
  }

  function handleMountCpp(editor, monaco) {
    cppEditorRef.current = editor;
    editor.updateOptions({
      readOnly: true,
      wordWrap: "on",
      minimap: { enabled: false },
      renderLineHighlight: "line",
      scrollBeyondLastLine: false,
    });
  }

  function copyCpp() {
    if (!cpp) return;
    navigator.clipboard.writeText(cpp);
  }

  function resetCode() {
    setCode("print('Hello')");
    pyEditorRef.current?.focus();
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ fontWeight: 600, opacity: 0.8 }}>Редактор</div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          <button className="btn ghost" type="button" onClick={resetCode}>
            Пример
          </button>
          <button
            className="btn secondary"
            type="button"
            onClick={copyCpp}
            disabled={!cpp}
          >
            Скопировать C++
          </button>
        </div>
      </div>

      {/* Сплит-панель */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `${split}% 8px ${100 - split}%`,
          gap: 8,
        }}
      >
        <div className="card" style={{ overflow: "hidden" }}>
          <div className="card-header">Python</div>
          <div className="card-body" style={{ padding: 0, height: 420 }}>
            <Editor
              height="100%"
              defaultLanguage="python"
              value={code}
              onChange={(v) => setCode(v ?? "")}
              onMount={handleMountPython}
              options={{}}
            />
          </div>
        </div>

        {/* Ручка ресайза */}
        <div
          title="Потяни, чтобы изменить ширину"
          style={{
            cursor: "col-resize",
            userSelect: "none",
            background: "rgba(255,255,255,.06)",
            borderRadius: 6,
          }}
          onMouseDown={(e) => {
            const startX = e.clientX;
            const container = e.currentTarget.parentElement;
            const total = (container?.clientWidth || 1000) - 8;
            const startSplit = split;
            const onMove = (ev) => {
              const dx = ev.clientX - startX;
              const deltaPct = (dx / total) * 100;
              const next = Math.max(20, Math.min(80, startSplit + deltaPct));
              setSplit(next);
            };
            const onUp = () => {
              window.removeEventListener("mousemove", onMove);
              window.removeEventListener("mouseup", onUp);
            };
            window.addEventListener("mousemove", onMove);
            window.addEventListener("mouseup", onUp);
          }}
        />

        <div className="card" style={{ overflow: "hidden" }}>
          <div className="card-header">Результат (C++)</div>
          <div className="card-body" style={{ padding: 0, height: 420 }}>
            <Editor
              height="100%"
              defaultLanguage="cpp"
              value={cpp || "// Результат появится здесь"}
              onMount={handleMountCpp}
              options={{}}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
