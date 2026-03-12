// src/App.jsx
import { useEffect, useRef, useState } from "react";
import { translate, API_BASE } from "./services/api";
import CodeEditors from "./components/CodeEditor";
import "./styles/App.css";

export default function App() {
  const [code, setCode] = useState(
    "def greet(name):\n    print('Hello, ' + name)\n\ngreet('World')\n",
  );
  const [cpp, setCpp] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [errors, setErrors] = useState([]);
  const [sourceFilename, setSourceFilename] = useState("translated.py");

  const fileInputRef = useRef(null);

  async function runTranslate() {
    setLoading(true);
    setErr("");
    setErrors([]);
    setCpp("");

    try {
      const out = await translate(code);
      setCpp(out);
    } catch (e) {
      if (e.errors) {
        setErrors(e.errors);
      } else {
        setErr(String(e?.message || e));
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      setCode(text);
      setSourceFilename(file.name);
      setErr("");
      setErrors([]);
    } catch {
      setErr("Не удалось прочитать файл");
    }

    // чтобы можно было загрузить тот же файл повторно
    e.target.value = "";
  }

  function handleExportCpp() {
    if (!cpp.trim()) return;

    const baseName =
      sourceFilename.replace(/\.[^/.]+$/, "") || "translated";

    const blob = new Blob([cpp], {
      type: "text/x-c++src;charset=utf-8",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${baseName}.cpp`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  // Горячая клавиша: Ctrl/Cmd+Enter
  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        runTranslate();
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [code]);

  return (
    <div className="app">
      <div className="header">
        <div className="title">Translator</div>
        <div className="badge">API: {API_BASE}</div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div
          className="card-body"
          style={{ display: "flex", gap: 8, flexWrap: "wrap" }}
        >
          <button className="btn" disabled={loading} onClick={runTranslate}>
            {loading ? "Перевожу…" : "Перевести (Ctrl+Enter)"}
          </button>

          <button
            className="btn secondary"
            type="button"
            onClick={() => fileInputRef.current?.click()}
          >
            Загрузить файл
          </button>

          <button
            className="btn secondary"
            type="button"
            disabled={!cpp.trim()}
            onClick={handleExportCpp}
          >
            Сохранить C++ в файл
          </button>

          <button className="btn secondary" onClick={() => setCpp("")}>
            Очистить результат
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept=".py,.txt"
            style={{ display: "none" }}
            onChange={handleFileChange}
          />
        </div>
      </div>

      {err && <div className="alert">Ошибка: {err}</div>}

      {errors.length > 0 && (
        <div className="alert error-list">
          <strong>Ошибки трансляции:</strong>
          <ul>
            {errors.map((err, i) => (
              <li key={i}>
                <strong>{err.type.toUpperCase()}</strong>
                {err.line !== null &&
                  err.line !== undefined &&
                  ` (строка ${err.line})`}
                : {err.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      <CodeEditors code={code} setCode={setCode} cpp={cpp} />
    </div>
  );
}