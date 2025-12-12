// src/App.jsx
import { useEffect, useState } from "react";
import { translate, API_BASE } from "./services/api";
import CodeEditors from "./components/CodeEditor";
import "./styles/App.css";

export default function App() {
  const [code, setCode] = useState(
    "def greet(name):\n    print('Hello, ' + name)\n\ngreet('World')\n"
  );
  const [cpp, setCpp] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  async function runTranslate() {
    setLoading(true);
    setErr("");
    setCpp("");
    try {
      const out = await translate(code);
      setCpp(out);
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoading(false);
    }
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
        <div className="card-body" style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className="btn" disabled={loading} onClick={runTranslate}>
            {loading ? "Перевожу…" : "Перевести (Ctrl+Enter)"}
          </button>
          <button className="btn secondary" onClick={() => setCpp("")}>
            Очистить результат
          </button>
        </div>
      </div>

      {err && <div className="alert">Ошибка: {err}</div>}

      <CodeEditors code={code} setCode={setCode} cpp={cpp} />
    </div>
  );
}
