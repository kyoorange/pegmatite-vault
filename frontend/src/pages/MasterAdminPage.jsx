import { useCallback, useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";

import {
  deleteMineral,
  deleteNamedMaster,
  listMinerals,
  listNamedMasters,
} from "../api/client";
import AdminResourceNav from "../components/AdminResourceNav";

const configs = {
  minerals: { title: "鉱物種", named: false },
  "mineral-classes": { title: "鉱物分類", named: true },
  "acquisition-methods": { title: "入手経路", named: true },
};

export default function MasterAdminPage() {
  const { resource } = useParams();
  const config = configs[resource];
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState("loading");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    if (!config) return;
    setStatus("loading");
    try {
      const payload = config.named
        ? await listNamedMasters(resource)
        : await listMinerals({ page: 1, page_size: 100 });
      setItems(config.named ? payload : payload.items);
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }, [config, resource]);

  useEffect(() => {
    load();
  }, [load]);

  if (!config) return <Navigate replace to="/404" />;

  async function handleDelete(item) {
    const name = item.name ?? item.japanese_name;
    if (!window.confirm(`「${name}」を削除しますか？`)) return;
    setMessage("");
    try {
      if (config.named) await deleteNamedMaster(resource, item.id);
      else await deleteMineral(item.id);
      await load();
    } catch (error) {
      setMessage(error.message);
    }
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
          <h2>{config.title}</h2>
          <p>{items.length}件</p>
        </div>
        <Link className="button button--primary" to={`/admin/${resource}/new`}>
          ＋ 新規登録
        </Link>
      </div>
      {message && <div className="form-error">{message}</div>}
      {status === "loading" && <div className="message-panel">読み込み中…</div>}
      {status === "error" && (
        <div className="message-panel message-panel--error">
          読み込みに失敗しました。
        </div>
      )}
      {status === "ready" && items.length === 0 && (
        <div className="empty-state empty-state--small">
          <p>データが登録されていません。</p>
        </div>
      )}
      {status === "ready" && items.length > 0 && (
        <div className="admin-list">
          {items.map((item) => (
            <div className="admin-row" key={item.id}>
              <div>
                <strong>{item.name ?? item.japanese_name}</strong>
                <small>
                  {item.english_name ??
                    item.description ??
                    item.mineral_class?.name ??
                    "詳細なし"}
                </small>
              </div>
              <span>
                {config.named ? "マスタ" : `${item.specimen_count}標本`}
              </span>
              <div className="button-group">
                <Link
                  className="button"
                  to={`/admin/${resource}/${item.id}/edit`}
                >
                  編集
                </Link>
                <button
                  className="button button--danger"
                  onClick={() => handleDelete(item)}
                  type="button"
                >
                  削除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
