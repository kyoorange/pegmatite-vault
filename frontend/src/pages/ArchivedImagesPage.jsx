import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import {
  archivedImageContentUrl,
  listArchivedImages,
  listSpecimens,
  permanentlyDeleteImage,
  restoreImage,
} from "../api/client";

function localDate(value) {
  return value ? new Date(value).toLocaleString() : "日時不明";
}

export default function ArchivedImagesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get("page") ?? 1);
  const [result, setResult] = useState({
    items: [],
    page: 1,
    page_size: 12,
    total: 0,
  });
  const [specimens, setSpecimens] = useState([]);
  const [targets, setTargets] = useState({});
  const [status, setStatus] = useState("loading");
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const [images, specimenPage] = await Promise.all([
        listArchivedImages({ page, page_size: 12 }),
        listSpecimens({
          page: 1,
          page_size: 100,
          sort: "specimen_name",
          order: "asc",
        }),
      ]);
      setResult(images);
      setSpecimens(specimenPage.items);
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }, [page]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleRestore(image) {
    const specimenId = targets[image.id];
    if (!specimenId) {
      setError("復元先の標本を選択してください。");
      return;
    }
    setBusyId(image.id);
    setError("");
    try {
      await restoreImage(image.id, specimenId);
      await load();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusyId(null);
    }
  }

  async function handlePermanentDelete(image) {
    const confirmed = window.confirm(
      `「${image.original_filename}」を完全削除しますか？\n\nDBレコード、オリジナル画像、表示用画像、サムネイルが削除され、元に戻せません。`,
    );
    if (!confirmed) return;
    setBusyId(image.id);
    setError("");
    try {
      await permanentlyDeleteImage(image.id);
      await load();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusyId(null);
    }
  }

  function moveToPage(nextPage) {
    setSearchParams({ page: nextPage });
  }

  return (
    <section className="page page--wide">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Image archive</p>
          <h1>アーカイブ画像</h1>
        </div>
        <Link className="button" to="/settings">
          SETTINGへ戻る
        </Link>
      </div>
      <p className="page-description">
        標本や画像から取り外された画像です。既存の標本へ復元するか、不要な画像を完全削除できます。
      </p>
      {error && <div className="form-error">{error}</div>}
      {status === "loading" && <div className="message-panel">読み込み中…</div>}
      {status === "error" && (
        <div className="message-panel message-panel--error">
          読み込みに失敗しました。
        </div>
      )}
      {status === "ready" && result.items.length === 0 && (
        <div className="empty-state">
          <p>アーカイブ画像はありません。</p>
        </div>
      )}
      {status === "ready" && result.items.length > 0 && (
        <>
          <p className="result-count">{result.total}件</p>
          <div className="archive-grid">
            {result.items.map((image) => (
              <article className="archive-card" key={image.id}>
                <img
                  alt={image.caption ?? image.original_filename}
                  src={archivedImageContentUrl(image.id)}
                />
                <div className="archive-card__body">
                  <strong>{image.original_filename}</strong>
                  <small>アーカイブ: {localDate(image.archived_at)}</small>
                  <small>
                    元の標本ID: {image.archived_from_specimen_id ?? "不明"}
                  </small>
                  <label>
                    復元先
                    <select
                      disabled={busyId === image.id}
                      onChange={(event) =>
                        setTargets((current) => ({
                          ...current,
                          [image.id]: event.target.value,
                        }))
                      }
                      value={targets[image.id] ?? ""}
                    >
                      <option value="">標本を選択</option>
                      {specimens.map((specimen) => (
                        <option key={specimen.id} value={specimen.id}>
                          No.{specimen.specimen_no} {specimen.specimen_name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="button-group">
                    <button
                      className="button button--primary"
                      disabled={busyId === image.id || specimens.length === 0}
                      onClick={() => handleRestore(image)}
                      type="button"
                    >
                      復元
                    </button>
                    <button
                      className="button button--danger"
                      disabled={busyId === image.id}
                      onClick={() => handlePermanentDelete(image)}
                      type="button"
                    >
                      完全削除
                    </button>
                  </div>
                </div>
              </article>
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
