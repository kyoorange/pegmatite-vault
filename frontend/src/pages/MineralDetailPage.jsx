import { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { getMineral, listMineralSpecimens } from "../api/client";
import SpecimenCard from "../components/SpecimenCard";

export default function MineralDetailPage() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get("page") ?? 1);
  const [mineral, setMineral] = useState(null);
  const [specimens, setSpecimens] = useState(null);
  const [status, setStatus] = useState("loading");

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const [mineralPayload, specimenPayload] = await Promise.all([
        getMineral(id),
        listMineralSpecimens(id, { page, page_size: 12 }),
      ]);
      setMineral(mineralPayload);
      setSpecimens(specimenPayload);
      setStatus("ready");
    } catch (error) {
      setStatus(error.status === 404 ? "not-found" : "error");
    }
  }, [id, page]);

  useEffect(() => {
    load();
  }, [load]);

  if (status === "loading")
    return <div className="message-panel">読み込み中…</div>;
  if (status === "not-found")
    return <div className="message-panel">鉱物が見つかりません。</div>;
  if (status === "error")
    return (
      <div className="message-panel message-panel--error">
        読み込みに失敗しました。
      </div>
    );

  return (
    <article className="page page--wide">
      <div className="page-heading">
        <div>
          <p className="eyebrow">{mineral.english_name ?? "Mineral detail"}</p>
          <h1>{mineral.japanese_name}</h1>
        </div>
      </div>
      <dl className="mineral-facts">
        <div>
          <dt>化学式</dt>
          <dd>{mineral.formula ?? "未設定"}</dd>
        </div>
        <div>
          <dt>結晶系</dt>
          <dd>{mineral.crystal_system ?? "未設定"}</dd>
        </div>
        <div>
          <dt>分類</dt>
          <dd>{mineral.mineral_class?.name ?? "未設定"}</dd>
        </div>
      </dl>
      <section className="mineral-description">
        <h2>説明</h2>
        <p>{mineral.description ?? "説明は登録されていません。"}</p>
      </section>
      <section className="home-section">
        <div className="section-heading">
          <div>
            <h2>関連標本</h2>
            <p>{specimens.total}件</p>
          </div>
        </div>
        {specimens.items.length > 0 ? (
          <>
            <div className="specimen-grid">
              {specimens.items.map((specimen) => (
                <SpecimenCard key={specimen.id} specimen={specimen} />
              ))}
            </div>
            <nav className="pagination" aria-label="ページ移動">
              <button
                className="button"
                disabled={page <= 1}
                onClick={() => setSearchParams({ page: page - 1 })}
              >
                前へ
              </button>
              <span>
                {page} /{" "}
                {Math.max(1, Math.ceil(specimens.total / specimens.page_size))}
              </span>
              <button
                className="button"
                disabled={page * specimens.page_size >= specimens.total}
                onClick={() => setSearchParams({ page: page + 1 })}
              >
                次へ
              </button>
            </nav>
          </>
        ) : (
          <div className="empty-state empty-state--small">
            <p>関連する標本はありません。</p>
          </div>
        )}
      </section>
      <Link className="back-link" to="/library">
        ← LIBRARYへ戻る
      </Link>
    </article>
  );
}
