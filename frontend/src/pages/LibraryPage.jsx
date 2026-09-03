import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { getMineralClassOptions, listMinerals } from "../api/client";

export default function LibraryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get("q") ?? "");
  const [classes, setClasses] = useState([]);
  const [result, setResult] = useState({
    items: [],
    page: 1,
    page_size: 24,
    total: 0,
  });
  const [status, setStatus] = useState("loading");
  const searchKey = searchParams.toString();
  const page = Number(searchParams.get("page") ?? 1);

  const load = useCallback(async () => {
    setStatus("loading");
    const params = new URLSearchParams(searchKey);
    try {
      const payload = await listMinerals({
        page,
        page_size: 24,
        q: params.get("q") ?? "",
        mineral_class_id: params.get("mineral_class_id") ?? "",
        sort: params.get("sort") ?? "japanese_name",
        order: params.get("order") ?? "asc",
      });
      setResult(payload);
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }, [page, searchKey]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    getMineralClassOptions().then(setClasses).catch(() => {});
  }, []);

  useEffect(() => {
    setQuery(searchParams.get("q") ?? "");
  }, [searchParams]);

  function updateParam(name, value) {
    const next = new URLSearchParams(searchParams);
    next.delete("page");
    if (value) next.set(name, value);
    else next.delete(name);
    setSearchParams(next);
  }

  function submitSearch(event) {
    event.preventDefault();
    updateParam("q", query.trim());
  }

  function moveToPage(nextPage) {
    const next = new URLSearchParams(searchParams);
    next.set("page", String(nextPage));
    setSearchParams(next);
  }

  return (
    <section className="page page--wide">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Mineral reference</p>
          <h1>LIBRARY</h1>
        </div>
      </div>
      <form className="search-bar" onSubmit={submitSearch}>
        <input
          aria-label="鉱物名を検索"
          onChange={(event) => setQuery(event.target.value)}
          placeholder="和名、英名、化学式で検索"
          value={query}
        />
        <button className="button button--primary" type="submit">
          検索
        </button>
      </form>
      <div className="library-toolbar">
        <div className="class-tabs" aria-label="鉱物分類">
          <button
            className={
              searchParams.has("mineral_class_id") ? "class-tab" : "class-tab is-active"
            }
            onClick={() => updateParam("mineral_class_id", "")}
            type="button"
          >
            すべて
          </button>
          {classes.map((mineralClass) => (
            <button
              className={
                searchParams.get("mineral_class_id") === String(mineralClass.id)
                  ? "class-tab is-active"
                  : "class-tab"
              }
              key={mineralClass.id}
              onClick={() =>
                updateParam("mineral_class_id", String(mineralClass.id))
              }
              type="button"
            >
              {mineralClass.name}
            </button>
          ))}
        </div>
        <div className="library-sort">
          <select
            aria-label="並び替え"
            onChange={(event) => updateParam("sort", event.target.value)}
            value={searchParams.get("sort") ?? "japanese_name"}
          >
            <option value="japanese_name">和名順</option>
            <option value="english_name">英名順</option>
            <option value="specimen_count">標本数順</option>
          </select>
          <select
            aria-label="昇順・降順"
            onChange={(event) => updateParam("order", event.target.value)}
            value={searchParams.get("order") ?? "asc"}
          >
            <option value="asc">昇順</option>
            <option value="desc">降順</option>
          </select>
        </div>
      </div>
      {status === "loading" && <div className="message-panel">読み込み中…</div>}
      {status === "error" && (
        <div className="message-panel message-panel--error">
          読み込みに失敗しました。
          <button className="text-button" onClick={load} type="button">
            再試行
          </button>
        </div>
      )}
      {status === "ready" && result.items.length === 0 && (
        <div className="empty-state">
          <p>条件に一致する鉱物がありません。</p>
        </div>
      )}
      {status === "ready" && result.items.length > 0 && (
        <>
          <p className="result-count">{result.total}件</p>
          <div className="mineral-list">
            {result.items.map((mineral) => (
              <Link
                className="mineral-row"
                key={mineral.id}
                to={`/minerals/${mineral.id}`}
              >
                <div>
                  <h2>{mineral.japanese_name}</h2>
                  <span>{mineral.english_name ?? "英名未設定"}</span>
                </div>
                <strong>{mineral.formula ?? "化学式未設定"}</strong>
                <span>{mineral.crystal_system ?? "結晶系未設定"}</span>
                <span>{mineral.mineral_class?.name ?? "分類未設定"}</span>
                <span>{mineral.specimen_count}標本</span>
              </Link>
            ))}
          </div>
          <nav className="pagination" aria-label="ページ移動">
            <button
              className="button"
              disabled={page <= 1}
              onClick={() => moveToPage(page - 1)}
            >
              前へ
            </button>
            <span>
              {page} / {Math.max(1, Math.ceil(result.total / result.page_size))}
            </span>
            <button
              className="button"
              disabled={page * result.page_size >= result.total}
              onClick={() => moveToPage(page + 1)}
            >
              次へ
            </button>
          </nav>
        </>
      )}
    </section>
  );
}
