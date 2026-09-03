import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  archiveImage,
  deleteSpecimen,
  getSpecimen,
  imageContentUrl,
  reorderSpecimenImages,
  uploadSpecimenImage,
} from "../api/client";

function DetailItem({ label, children }) {
  return (
    <div className="detail-item">
      <dt>{label}</dt>
      <dd>{children || "未設定"}</dd>
    </div>
  );
}

export default function SpecimenDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [specimen, setSpecimen] = useState(null);
  const [status, setStatus] = useState("loading");
  const [deleting, setDeleting] = useState(false);
  const [selectedImageId, setSelectedImageId] = useState(null);
  const [imageBusy, setImageBusy] = useState(false);
  const [imageError, setImageError] = useState("");

  const loadSpecimen = useCallback(async () => {
    try {
      const payload = await getSpecimen(id);
      setSpecimen(payload);
      setSelectedImageId((current) =>
        payload.images.some((image) => image.id === current)
          ? current
          : (payload.images[0]?.id ?? null),
      );
      setStatus("ready");
    } catch (error) {
      setStatus(error.status === 404 ? "not-found" : "error");
    }
  }, [id]);

  useEffect(() => {
    loadSpecimen();
  }, [loadSpecimen]);

  async function handleImageUpload(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setImageBusy(true);
    setImageError("");
    try {
      const image = await uploadSpecimenImage(id, file);
      await loadSpecimen();
      setSelectedImageId(image.id);
    } catch (error) {
      setImageError(error.message);
    } finally {
      setImageBusy(false);
    }
  }

  async function handleMakePrimary() {
    if (!selectedImageId || specimen.images[0]?.id === selectedImageId) return;
    const imageIds = [
      selectedImageId,
      ...specimen.images
        .map((image) => image.id)
        .filter((imageId) => imageId !== selectedImageId),
    ];
    setImageBusy(true);
    setImageError("");
    try {
      await reorderSpecimenImages(id, imageIds);
      await loadSpecimen();
    } catch (error) {
      setImageError(error.message);
    } finally {
      setImageBusy(false);
    }
  }

  async function handleImageArchive() {
    if (!selectedImageId || !window.confirm("選択中の画像をアーカイブしますか？"))
      return;
    setImageBusy(true);
    setImageError("");
    try {
      await archiveImage(selectedImageId);
      await loadSpecimen();
    } catch (error) {
      setImageError(error.message);
    } finally {
      setImageBusy(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm(`「${specimen.specimen_name}」を削除しますか？`))
      return;
    setDeleting(true);
    try {
      await deleteSpecimen(id);
      navigate("/vault", { replace: true });
    } catch {
      setDeleting(false);
      window.alert("削除に失敗しました。");
    }
  }

  if (status === "loading")
    return <div className="message-panel">読み込み中…</div>;
  if (status === "not-found")
    return <div className="message-panel">標本が見つかりません。</div>;
  if (status === "error") {
    return (
      <div className="message-panel message-panel--error">
        読み込みに失敗しました。
      </div>
    );
  }

  return (
    <article className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Specimen No. {specimen.specimen_no}</p>
          <h1>{specimen.specimen_name}</h1>
        </div>
        <div className="button-group">
          <Link className="button" to={`/specimens/${id}/edit`}>
            編集
          </Link>
          <button
            className="button button--danger"
            disabled={deleting}
            onClick={handleDelete}
          >
            {deleting ? "削除中…" : "削除"}
          </button>
        </div>
      </div>
      <div className="detail-layout">
        <section className="image-gallery" aria-label="標本画像">
          <div className="image-gallery__main">
            {selectedImageId ? (
              <img
                alt={`${specimen.specimen_name}の画像`}
                src={imageContentUrl(selectedImageId, "display")}
              />
            ) : (
              <div className="image-placeholder">NO IMAGE</div>
            )}
          </div>
          {specimen.images.length > 0 && (
            <div className="image-gallery__thumbnails">
              {specimen.images.map((image, index) => (
                <button
                  aria-label={`画像${index + 1}を表示`}
                  className={
                    image.id === selectedImageId
                      ? "image-thumbnail image-thumbnail--selected"
                      : "image-thumbnail"
                  }
                  key={image.id}
                  onClick={() => setSelectedImageId(image.id)}
                  type="button"
                >
                  <img alt="" src={imageContentUrl(image.id)} />
                </button>
              ))}
            </div>
          )}
          <div className="image-gallery__actions">
            <label className="button button--primary">
              {imageBusy ? "処理中…" : "画像を追加"}
              <input
                accept="image/jpeg,image/png,image/webp"
                className="visually-hidden"
                disabled={imageBusy}
                onChange={handleImageUpload}
                type="file"
              />
            </label>
            {selectedImageId && (
              <>
                <button
                  className="button"
                  disabled={
                    imageBusy || specimen.images[0]?.id === selectedImageId
                  }
                  onClick={handleMakePrimary}
                  type="button"
                >
                  サムネにする  
                </button>
                <button
                  className="button button--danger"
                  disabled={imageBusy}
                  onClick={handleImageArchive}
                  type="button"
                >
                  アーカイブ
                </button>
              </>
            )}
          </div>
          {imageError && <p className="form-error">{imageError}</p>}
        </section>
        <dl className="detail-list">
          <DetailItem label="お気に入り">
            {specimen.favorite ? "★ 登録済み" : "未登録"}
          </DetailItem>
          <DetailItem label="鉱物">
            {specimen.minerals.map((mineral, index) => (
              <span key={mineral.id}>
                {index > 0 && "、"}
                <Link to={`/minerals/${mineral.id}`}>
                  {mineral.japanese_name}
                </Link>
              </span>
            ))}
          </DetailItem>
          <DetailItem label="採集地">
            {specimen.locality && (
              <Link to={`/localities/${specimen.locality.id}`}>
                {specimen.locality.locality_name}
              </Link>
            )}
          </DetailItem>
          <DetailItem label="入手経路">
            {specimen.acquisition_method?.name}
          </DetailItem>
          <DetailItem label="入手日">{specimen.collection_date}</DetailItem>
          <DetailItem label="特徴">{specimen.features}</DetailItem>
          <DetailItem label="備考">{specimen.note}</DetailItem>
        </dl>
      </div>
      <Link className="back-link" to="/vault">
        ← VAULTへ戻る
      </Link>
    </article>
  );
}
