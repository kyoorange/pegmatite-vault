import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { deleteLocality, listLocalities } from "../api/client";
import AdminResourceNav from "../components/AdminResourceNav";


export default function AdminPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get("q") ?? "");
  const page = Number(searchParams.get("page") ?? 1);
  const searchKey = searchParams.toString();
  const [result, setResult] = useState({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
  });
  const [status, setStatus] = useState("loading");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const params = new URLSearchParams(searchKey);
      const payload = await listLocalities({
        page,
        page_size: 20,
        q: params.get("q") ?? "",
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

  async function handleDelete(locality) {
    if (!window.confirm(`「${locality.locality_name}」を削除しますか？`)) return;
    setMessage("");
    try {
      await deleteLocality(locality.id);
      await load();
    } catch (error) {
      setMessage(error.message);
    }
  }

  function submitSearch(event) {
    event.preventDefault();
    setSearchParams(query.trim() ? { q: query.trim() } : {});
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
          <p className="eyebrow">Master data</p>
          <h1>ADMIN</h1>
        </div>
      </div>
      <AdminResourceNav />
      <div className="section-heading admin-section-heading">
        <div>
          <h2>採集地</h2>
          <p>標本登録時に選択する採集地を管理します。</p>
        </div>
        <Link className="button button--primary" to="/admin/localities/new">
          ＋ 新規登録
        </Link>
      </div>
      <form className="search-bar" onSubmit={submitSearch}>
        <input
          aria-label="採集地を検索"
          onChange={(event) => setQuery(event.target.value)}
          placeholder="地名・通称・備考で検索"
          value={query}
        />
        <button className="button" type="submit">
          検索
        </button>
      </form>
      {message && <div className="form-error">{message}</div>}
      {status === "loading" && <div className="message-panel">読み込み中…</div>}
      {status === "error" && (
        <div className="message-panel message-panel--error">
          読み込みに失敗しました。
        </div>
      )}
      {status === "ready" && result.items.length === 0 && (
        <div className="empty-state empty-state--small">
          <p>採集地が登録されていません。</p>
        </div>
      )}
      {status === "ready" && result.items.length > 0 && (
        <>
          <div className="admin-list">
            {result.items.map((locality) => (
              <div className="admin-row" key={locality.id}>
                <div>
                  <Link to={`/localities/${locality.id}`}>
                    {locality.locality_name}
                  </Link>
                  <small>{locality.alias_name ?? "通称なし"}</small>
                </div>
                <span>{locality.specimen_count}標本</span>
                <div className="button-group">
                  <Link
                    className="button"
                    to={`/admin/localities/${locality.id}/edit`}
                  >
                    編集
                  </Link>
                  <button
                    className="button button--danger"
                    onClick={() => handleDelete(locality)}
                    type="button"
                  >
                    削除
                  </button>
                </div>
              </div>
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
