import { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { getLocality, listLocalitySpecimens } from "../api/client";
import SpecimenCard from "../components/SpecimenCard";

export default function LocalityDetailPage() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get("page") ?? 1);
  const [locality, setLocality] = useState(null);
  const [specimens, setSpecimens] = useState(null);
  const [status, setStatus] = useState("loading");

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const [localityPayload, specimenPayload] = await Promise.all([
        getLocality(id),
        listLocalitySpecimens(id, { page, page_size: 12 }),
      ]);
      setLocality(localityPayload);
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
    return <div className="message-panel">採集地が見つかりません。</div>;
  if (status === "error")
    return (
      <div className="message-panel message-panel--error">
        読み込みに失敗しました。
      </div>
    );

  const hasCoordinates =
    locality.latitude !== null && locality.longitude !== null;
  const mapUrl = hasCoordinates
    ? `https://www.openstreetmap.org/?mlat=${locality.latitude}&mlon=${locality.longitude}#map=15/${locality.latitude}/${locality.longitude}`
    : null;

  return (
    <article className="page page--wide">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Locality detail</p>
          <h1>{locality.locality_name}</h1>
        </div>
      </div>
      <dl className="mineral-facts">
        <div>
          <dt>通称</dt>
          <dd>{locality.alias_name ?? "未設定"}</dd>
        </div>
        <div>
          <dt>緯度・経度</dt>
          <dd>
            {hasCoordinates
              ? `${locality.latitude}, ${locality.longitude}`
              : "未設定"}
          </dd>
        </div>
        <div>
          <dt>地図</dt>
          <dd>
            {mapUrl ? (
              <a href={mapUrl} rel="noreferrer" target="_blank">
                OpenStreetMapで開く ↗
              </a>
            ) : (
              "座標未設定"
            )}
          </dd>
        </div>
      </dl>
      <section className="mineral-description">
        <h2>備考</h2>
        <p>{locality.note ?? "備考は登録されていません。"}</p>
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
      <Link className="back-link" to="/vault">
        ← VAULTへ戻る
      </Link>
    </article>
  );
}
