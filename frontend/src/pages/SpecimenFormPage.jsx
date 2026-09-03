import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  createSpecimen,
  getSpecimen,
  getSpecimenOptions,
  updateSpecimen,
} from "../api/client";

const emptyForm = {
  specimen_no: "",
  specimen_name: "",
  locality_id: "",
  acquisition_method_id: "",
  collection_date: "",
  features: "",
  note: "",
  favorite: false,
  mineral_ids: [],
};

function toPayload(form) {
  return {
    specimen_no: form.specimen_no === "" ? null : Number(form.specimen_no),
    specimen_name: form.specimen_name.trim(),
    locality_id: form.locality_id || null,
    acquisition_method_id: form.acquisition_method_id
      ? Number(form.acquisition_method_id)
      : null,
    collection_date: form.collection_date || null,
    features: form.features.trim() || null,
    note: form.note.trim() || null,
    favorite: form.favorite,
    mineral_ids: form.mineral_ids,
  };
}

export default function SpecimenFormPage() {
  const { id } = useParams();
  const editing = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState(emptyForm);
  const [options, setOptions] = useState({
    minerals: [],
    localities: [],
    acquisitionMethods: [],
  });
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      getSpecimenOptions(),
      editing ? getSpecimen(id) : Promise.resolve(null),
    ])
      .then(([loadedOptions, specimen]) => {
        setOptions(loadedOptions);
        if (specimen) {
          setForm({
            specimen_no: String(specimen.specimen_no),
            specimen_name: specimen.specimen_name,
            locality_id: specimen.locality?.id ?? "",
            acquisition_method_id: specimen.acquisition_method?.id
              ? String(specimen.acquisition_method.id)
              : "",
            collection_date: specimen.collection_date ?? "",
            features: specimen.features ?? "",
            note: specimen.note ?? "",
            favorite: specimen.favorite,
            mineral_ids: specimen.minerals.map((mineral) => mineral.id),
          });
        }
        setStatus("ready");
      })
      .catch(() => {
        setError("フォームの準備に失敗しました。");
        setStatus("error");
      });
  }, [editing, id]);

  function updateField(event) {
    const { name, value, checked, type } = event.target;
    setForm((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function toggleMineral(mineralId) {
    setForm((current) => ({
      ...current,
      mineral_ids: current.mineral_ids.includes(mineralId)
        ? current.mineral_ids.filter((value) => value !== mineralId)
        : [...current.mineral_ids, mineralId],
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!form.specimen_name.trim()) {
      setError("標本名を入力してください。");
      return;
    }
    setStatus("saving");
    setError("");
    try {
      const specimen = editing
        ? await updateSpecimen(id, toPayload(form))
        : await createSpecimen(toPayload(form));
      navigate(`/specimens/${specimen.id}`, { replace: true });
    } catch (requestError) {
      setError(requestError.message);
      setStatus("ready");
    }
  }

  if (status === "loading")
    return <div className="message-panel">読み込み中…</div>;

  return (
    <section className="page">
      <p className="eyebrow">{editing ? "Edit specimen" : "New specimen"}</p>
      <h1>{editing ? "標本を編集" : "標本を登録"}</h1>
      {error && <div className="form-error">{error}</div>}
      <form className="specimen-form" onSubmit={handleSubmit}>
        <div className="form-grid">
          <label>
            標本番号
            <input
              min="1"
              name="specimen_no"
              type="number"
              value={form.specimen_no}
              onChange={updateField}
              placeholder="未入力なら自動採番"
            />
          </label>
          <label>
            標本名 <span className="required">*</span>
            <input
              required
              maxLength="255"
              name="specimen_name"
              value={form.specimen_name}
              onChange={updateField}
            />
          </label>
          <label>
            採集地
            <select
              name="locality_id"
              value={form.locality_id}
              onChange={updateField}
            >
              <option value="">未設定</option>
              {options.localities.map((locality) => (
                <option key={locality.id} value={locality.id}>
                  {locality.locality_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            入手経路
            <select
              name="acquisition_method_id"
              value={form.acquisition_method_id}
              onChange={updateField}
            >
              <option value="">未設定</option>
              {options.acquisitionMethods.map((method) => (
                <option key={method.id} value={method.id}>
                  {method.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            入手日
            <input
              name="collection_date"
              type="date"
              value={form.collection_date}
              onChange={updateField}
            />
          </label>
          <label className="checkbox-label">
            <input
              checked={form.favorite}
              name="favorite"
              type="checkbox"
              onChange={updateField}
            />
            お気に入り
          </label>
        </div>
        <fieldset>
          <legend>鉱物</legend>
          {options.minerals.length === 0 ? (
            <p className="field-help">登録済みの鉱物がありません。</p>
          ) : (
            <div className="checkbox-grid">
              {options.minerals.map((mineral) => (
                <label key={mineral.id} className="checkbox-label">
                  <input
                    checked={form.mineral_ids.includes(mineral.id)}
                    type="checkbox"
                    onChange={() => toggleMineral(mineral.id)}
                  />
                  {mineral.japanese_name}
                </label>
              ))}
            </div>
          )}
        </fieldset>
        <label>
          特徴
          <textarea
            name="features"
            rows="4"
            value={form.features}
            onChange={updateField}
          />
        </label>
        <label>
          備考
          <textarea
            name="note"
            rows="4"
            value={form.note}
            onChange={updateField}
          />
        </label>
        <div className="form-actions">
          <Link className="button" to={editing ? `/specimens/${id}` : "/vault"}>
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
