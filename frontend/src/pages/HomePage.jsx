import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listSpecimens } from "../api/client";
import SpecimenCard from "../components/SpecimenCard";

function SpecimenSection({ title, description, specimens, emptyMessage }) {
  return (
    <section className="home-section">
      <div className="section-heading">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
        <Link to="/vault">すべて見る →</Link>
      </div>
      {specimens.length > 0 ? (
        <div className="specimen-grid specimen-grid--compact">
          {specimens.map((specimen) => (
            <SpecimenCard key={specimen.id} specimen={specimen} />
          ))}
        </div>
      ) : (
        <div className="empty-state empty-state--small">
          <p>{emptyMessage}</p>
        </div>
      )}
    </section>
  );
}

export default function HomePage() {
  const [result, setResult] = useState({ favorites: [], recent: [] });
  const [status, setStatus] = useState("loading");

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const [favorites, recent] = await Promise.all([
        listSpecimens({
          page: 1,
          page_size: 4,
          favorite: true,
          sort: "created_at",
          order: "desc",
        }),
        listSpecimens({
          page: 1,
          page_size: 4,
          sort: "created_at",
          order: "desc",
        }),
      ]);
      setResult({ favorites: favorites.items, recent: recent.items });
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <section className="page page--wide">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Collection overview</p>
          <h1>HOME</h1>
        </div>
        <Link className="button button--primary" to="/specimens/new">
          ＋ 標本を追加
        </Link>
      </div>
      {status === "loading" && <div className="message-panel">読み込み中…</div>}
      {status === "error" && (
        <div className="message-panel message-panel--error">
          読み込みに失敗しました。
          <button className="text-button" type="button" onClick={load}>
            再試行
          </button>
        </div>
      )}
      {status === "ready" && (
        <div className="home-sections">
          <SpecimenSection
            emptyMessage="お気に入りの標本はまだありません。"
            specimens={result.favorites}
            title="お気に入り"
          />
          <SpecimenSection
            emptyMessage="登録済みの標本はまだありません。"
            specimens={result.recent}
            title="最近追加した標本"
          />
        </div>
      )}
    </section>
  );
}
