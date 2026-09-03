import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { createLocality, getLocality, updateLocality } from "../api/client";

const emptyForm = {
  locality_name: "",
  alias_name: "",
  latitude: "",
  longitude: "",
  note: "",
};

function toPayload(form) {
  return {
    locality_name: form.locality_name.trim(),
    alias_name: form.alias_name.trim() || null,
    latitude: form.latitude === "" ? null : Number(form.latitude),
    longitude: form.longitude === "" ? null : Number(form.longitude),
    note: form.note.trim() || null,
  };
}

export default function LocalityFormPage() {
  const { id } = useParams();
  const editing = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState(emptyForm);
  const [status, setStatus] = useState(editing ? "loading" : "ready");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!editing) return;
    getLocality(id)
      .then((locality) => {
        setForm({
          locality_name: locality.locality_name,
          alias_name: locality.alias_name ?? "",
          latitude:
            locality.latitude === null ? "" : String(locality.latitude),
          longitude:
            locality.longitude === null ? "" : String(locality.longitude),
          note: locality.note ?? "",
        });
        setStatus("ready");
      })
      .catch(() => {
        setError("採集地の読み込みに失敗しました。");
        setStatus("error");
      });
  }, [editing, id]);

  function updateField(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus("saving");
    setError("");
    try {
      const locality = editing
        ? await updateLocality(id, toPayload(form))
        : await createLocality(toPayload(form));
      navigate(`/localities/${locality.id}`, { replace: true });
    } catch (requestError) {
      setError(requestError.message);
      setStatus("ready");
    }
  }

  if (status === "loading")
    return <div className="message-panel">読み込み中…</div>;

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">{editing ? "Edit locality" : "New locality"}</p>
          <h1>{editing ? "採集地を編集" : "採集地を登録"}</h1>
        </div>
      </div>
      {error && <div className="form-error">{error}</div>}
      <form className="specimen-form" onSubmit={handleSubmit}>
        <div className="form-grid">
          <label>
            地名 <span className="required">*</span>
            <input
              maxLength="255"
              name="locality_name"
              onChange={updateField}
              required
              value={form.locality_name}
            />
          </label>
          <label>
            通称
            <input
              maxLength="255"
              name="alias_name"
              onChange={updateField}
              value={form.alias_name}
            />
          </label>
          <label>
            緯度
            <input
              max="90"
              min="-90"
              name="latitude"
              onChange={updateField}
              step="0.0000001"
              type="number"
              value={form.latitude}
            />
          </label>
          <label>
            経度
            <input
              max="180"
              min="-180"
              name="longitude"
              onChange={updateField}
              step="0.0000001"
              type="number"
              value={form.longitude}
            />
          </label>
        </div>
        <label>
          備考
          <textarea
            name="note"
            onChange={updateField}
            rows="6"
            value={form.note}
          />
        </label>
        <div className="form-actions">
          <Link className="button" to="/admin">
            キャンセル
          </Link>
          <button
            className="button button--primary"
            disabled={status === "saving"}
            type="submit"
          >
            {status === "saving" ? "保存中…" : "保存"}
          </button>
        </div>
      </form>
    </section>
  );
}
