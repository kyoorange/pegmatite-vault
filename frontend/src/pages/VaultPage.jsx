import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { getSpecimenOptions, listSpecimens } from "../api/client";
import SpecimenCard from "../components/SpecimenCard";

function filtersFromParams(searchParams) {
  return {
    q: searchParams.get("q") ?? "",
    mineral_id: searchParams.get("mineral_id") ?? "",
    locality_id: searchParams.get("locality_id") ?? "",
    acquisition_method_id: searchParams.get("acquisition_method_id") ?? "",
    favorite: searchParams.get("favorite") ?? "",
    sort: searchParams.get("sort") ?? "created_at",
    order: searchParams.get("order") ?? "desc",
  };
}

export default function VaultPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState(() => filtersFromParams(searchParams));
  const [options, setOptions] = useState({
    minerals: [],
    localities: [],
    acquisitionMethods: [],
  });
  const [result, setResult] = useState({
    items: [],
    page: 1,
    page_size: 24,
    total: 0,
  });
  const [status, setStatus] = useState("loading");
  const page = Number(searchParams.get("page") ?? 1);
  const view = searchParams.get("view") === "list" ? "list" : "grid";
  const searchKey = searchParams.toString();

  const load = useCallback(() => {
    setStatus("loading");
    const activeFilters = filtersFromParams(new URLSearchParams(searchKey));
    listSpecimens({ page, page_size: 24, ...activeFilters })
      .then((payload) => {
        setResult(payload);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, [page, searchKey]);

  useEffect(() => load(), [load]);

  useEffect(() => {
    getSpecimenOptions().then(setOptions).catch(() => {});
  }, []);

  useEffect(() => {
    setFilters(filtersFromParams(searchParams));
  }, [searchParams]);

  function submitSearch(event) {
    event.preventDefault();
    const nextParams = {};
    Object.entries(filters).forEach(([key, value]) => {
      const normalized = typeof value === "string" ? value.trim() : value;
      if (
        normalized !== "" &&
        !(
          (key === "sort" && normalized === "created_at") ||
          (key === "order" && normalized === "desc")
        )
      ) {
        nextParams[key] = normalized;
      }
    });
    if (view === "list") {
      nextParams.view = "list";
    }
    setSearchParams(nextParams);
  }

  function moveToPage(nextPage) {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("page", String(nextPage));
    setSearchParams(nextParams);
  }

  function updateFilter(event) {
    setFilters((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  function resetFilters() {
    setSearchParams(view === "list" ? { view: "list" } : {});
  }

  function changeView(nextView) {
    const nextParams = new URLSearchParams(searchParams);
    if (nextView === "list") {
      nextParams.set("view", "list");
    } else {
      nextParams.delete("view");
    }
    setSearchParams(nextParams, { replace: true });
  }

  return (
    <section className="page page--wide">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Collection</p>
          <h1>VAULT</h1>
        </div>
        <Link className="button button--primary" to="/specimens/new">
          ＋ 標本を追加
        </Link>
      </div>
      <form className="vault-filters" onSubmit={submitSearch}>
        <div className="search-bar">
          <label className="visually-hidden" htmlFor="specimen-search">
            標本を検索
          </label>
          <input
            id="specimen-search"
            name="q"
            value={filters.q}
            onChange={updateFilter}
            placeholder="標本名、番号、鉱物、採集地で検索"
          />
          <button className="button button--primary" type="submit">
            検索
          </button>
        </div>
        <div className="filter-grid">
          <select
            aria-label="鉱物で絞り込み"
            name="mineral_id"
            onChange={updateFilter}
            value={filters.mineral_id}
          >
            <option value="">すべての鉱物</option>
            {options.minerals.map((mineral) => (
              <option key={mineral.id} value={mineral.id}>
                {mineral.japanese_name}
              </option>
            ))}
          </select>
          <select
            aria-label="採集地で絞り込み"
            name="locality_id"
            onChange={updateFilter}
            value={filters.locality_id}
          >
            <option value="">すべての採集地</option>
            {options.localities.map((locality) => (
              <option key={locality.id} value={locality.id}>
                {locality.locality_name}
              </option>
            ))}
          </select>
          <select
            aria-label="入手経路で絞り込み"
            name="acquisition_method_id"
            onChange={updateFilter}
            value={filters.acquisition_method_id}
          >
            <option value="">すべての入手経路</option>
            {options.acquisitionMethods.map((method) => (
              <option key={method.id} value={method.id}>
                {method.name}
              </option>
            ))}
          </select>
          <select
            aria-label="お気に入りで絞り込み"
            name="favorite"
            onChange={updateFilter}
            value={filters.favorite}
          >
            <option value="">お気に入り指定なし</option>
            <option value="true">お気に入りのみ</option>
            <option value="false">お気に入り以外</option>
          </select>
          <select
            aria-label="並び順"
            name="sort"
            onChange={updateFilter}
            value={filters.sort}
          >
            <option value="created_at">登録日時</option>
            <option value="specimen_no">標本番号</option>
            <option value="specimen_name">標本名</option>
          </select>
          <select
            aria-label="昇順・降順"
            name="order"
            onChange={updateFilter}
            value={filters.order}
          >
            <option value="desc">降順</option>
            <option value="asc">昇順</option>
          </select>
          <button className="button" type="submit">
            条件を適用
          </button>
          <button className="button" onClick={resetFilters} type="button">
            リセット
          </button>
        </div>
      </form>
      {status === "loading" && <div className="message-panel">読み込み中…</div>}
      {status === "error" && (
        <div className="message-panel message-panel--error">
          読み込みに失敗しました。
          <button className="text-button" type="button" onClick={load}>
            再試行
          </button>
        </div>
      )}
      {status === "ready" && result.items.length === 0 && (
        <div className="empty-state">
          <p>条件に一致する標本がありません。</p>
          <Link to="/specimens/new">最初の標本を登録する</Link>
        </div>
      )}
      {status === "ready" && result.items.length > 0 && (
        <>
          <div className="result-toolbar">
            <p className="result-count">{result.total}件</p>
            <div className="view-switch" role="group" aria-label="表示形式">
              <button
                aria-pressed={view === "grid"}
                className={
                  view === "grid"
                    ? "view-switch__button is-active"
                    : "view-switch__button"
                }
                onClick={() => changeView("grid")}
                title="グリッド表示"
                type="button"
              >
                <span aria-hidden="true">▦</span>
                グリッド
              </button>
              <button
                aria-pressed={view === "list"}
                className={
                  view === "list"
                    ? "view-switch__button is-active"
                    : "view-switch__button"
                }
                onClick={() => changeView("list")}
                title="リスト表示"
                type="button"
              >
                <span aria-hidden="true">☷</span>
                リスト
              </button>
            </div>
          </div>
          <div
            className={
              view === "list"
                ? "specimen-grid specimen-grid--list"
                : "specimen-grid"
            }
          >
            {result.items.map((specimen) => (
              <SpecimenCard
                key={specimen.id}
                specimen={specimen}
                view={view}
              />
            ))}
          </div>
          <nav className="pagination" aria-label="ページ移動">
            <button
              className="button"
              disabled={result.page <= 1}
              onClick={() => moveToPage(page - 1)}
            >
              前へ
            </button>
            <span>
              {result.page} /{" "}
              {Math.max(1, Math.ceil(result.total / result.page_size))}
            </span>
            <button
              className="button"
              disabled={result.page * result.page_size >= result.total}
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
