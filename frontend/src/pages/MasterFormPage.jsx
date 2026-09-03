import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";

import {
  createMineral,
  createNamedMaster,
  getMineral,
  getMineralClassOptions,
  getNamedMaster,
  updateMineral,
  updateNamedMaster,
} from "../api/client";

const configs = {
  minerals: { title: "鉱物種", named: false },
  "mineral-classes": { title: "鉱物分類", named: true },
  "acquisition-methods": { title: "入手経路", named: true },
};

const emptyNamed = { name: "", description: "" };
const emptyMineral = {
  japanese_name: "",
  english_name: "",
  formula: "",
  crystal_system: "",
  mineral_class_id: "",
  description: "",
};

function nullable(value) {
  return value.trim() || null;
}

export default function MasterFormPage() {
  const { resource, id } = useParams();
  const config = configs[resource];
  const editing = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState(config?.named ? emptyNamed : emptyMineral);
  const [classes, setClasses] = useState([]);
  const [status, setStatus] = useState(editing ? "loading" : "ready");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!config) return;
    Promise.all([
      config.named ? Promise.resolve([]) : getMineralClassOptions(),
      editing
        ? config.named
          ? getNamedMaster(resource, id)
          : getMineral(id)
        : Promise.resolve(null),
    ])
      .then(([classOptions, item]) => {
        setClasses(classOptions);
        if (item) {
          setForm(
            config.named
              ? {
                  name: item.name,
                  description: item.description ?? "",
                }
              : {
                  japanese_name: item.japanese_name,
                  english_name: item.english_name ?? "",
                  formula: item.formula ?? "",
                  crystal_system: item.crystal_system ?? "",
                  mineral_class_id: item.mineral_class
                    ? String(item.mineral_class.id)
                    : "",
                  description: item.description ?? "",
                },
          );
        }
        setStatus("ready");
      })
      .catch(() => {
        setError("データの読み込みに失敗しました。");
        setStatus("error");
      });
  }, [config, editing, id, resource]);

  if (!config) return <Navigate replace to="/404" />;

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
      const payload = config.named
        ? {
            name: form.name.trim(),
            description: nullable(form.description),
          }
        : {
            japanese_name: form.japanese_name.trim(),
            english_name: nullable(form.english_name),
            formula: nullable(form.formula),
            crystal_system: nullable(form.crystal_system),
            mineral_class_id: form.mineral_class_id
              ? Number(form.mineral_class_id)
              : null,
            description: nullable(form.description),
          };
      if (config.named) {
        if (editing) await updateNamedMaster(resource, id, payload);
        else await createNamedMaster(resource, payload);
      } else if (editing) {
        await updateMineral(id, payload);
      } else {
        await createMineral(payload);
      }
      navigate(`/admin/${resource}`, { replace: true });
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
          <p className="eyebrow">{editing ? "Edit master" : "New master"}</p>
          <h1>
            {config.title}を{editing ? "編集" : "登録"}
          </h1>
        </div>
      </div>
      {error && <div className="form-error">{error}</div>}
      <form className="specimen-form" onSubmit={handleSubmit}>
        {config.named ? (
          <label>
            名称 <span className="required">*</span>
            <input
              maxLength="255"
              name="name"
              onChange={updateField}
              required
              value={form.name}
            />
          </label>
        ) : (
          <div className="form-grid">
            <label>
              和名 <span className="required">*</span>
              <input
                maxLength="255"
                name="japanese_name"
                onChange={updateField}
                required
                value={form.japanese_name}
              />
            </label>
            <label>
              英名
              <input
                maxLength="255"
                name="english_name"
                onChange={updateField}
                value={form.english_name}
              />
            </label>
            <label>
              化学式
              <input
                maxLength="255"
                name="formula"
                onChange={updateField}
                value={form.formula}
              />
            </label>
            <label>
              結晶系
              <input
                maxLength="100"
                name="crystal_system"
                onChange={updateField}
                value={form.crystal_system}
              />
            </label>
            <label>
              鉱物分類
              <select
                name="mineral_class_id"
                onChange={updateField}
                value={form.mineral_class_id}
              >
                <option value="">未設定</option>
                {classes.map((mineralClass) => (
                  <option key={mineralClass.id} value={mineralClass.id}>
                    {mineralClass.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
        <label>
          説明
          <textarea
            name="description"
            onChange={updateField}
            rows="6"
            value={form.description}
          />
        </label>
        <div className="form-actions">
          <Link className="button" to={`/admin/${resource}`}>
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
