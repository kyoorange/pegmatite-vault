import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  commitDataImport,
  exportData,
  getSystemStatus,
  migrateImageStorage,
  validateDataImport,
  validateImageStorageTarget,
} from "../api/client";

function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const exponent = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );
  return `${(bytes / 1024 ** exponent).toFixed(exponent === 0 ? 0 : 1)} ${units[exponent]}`;
}

function StatusItem({ label, children }) {
  return (
    <div className="settings-status__item">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

export default function SettingsPage() {
  const [system, setSystem] = useState(null);
  const [status, setStatus] = useState("loading");
  const [exporting, setExporting] = useState(false);
  const [actionError, setActionError] = useState("");
  const [importValidation, setImportValidation] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importMessage, setImportMessage] = useState("");
  const [storagePath, setStoragePath] = useState("");
  const [storagePreview, setStoragePreview] = useState(null);
  const [storageBusy, setStorageBusy] = useState(false);
  const [storageMessage, setStorageMessage] = useState("");

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      setSystem(await getSystemStatus());
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleExport() {
    setExporting(true);
    setActionError("");
    try {
      const { blob, filename } = await exportData();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setActionError(error.message);
    } finally {
      setExporting(false);
    }
  }

  async function handleImportFile(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setImporting(true);
    setActionError("");
    setImportMessage("");
    setImportValidation(null);
    try {
      setImportValidation(await validateDataImport(file));
    } catch (error) {
      setActionError(error.message);
    } finally {
      setImporting(false);
    }
  }

  async function handleImportCommit() {
    if (
      !importValidation?.commit_token ||
      !window.confirm(
        "検証結果の内容をインポートしますか？既存データと同じIDの行は更新されます。",
      )
    )
      return;
    setImporting(true);
    setActionError("");
    try {
      const result = await commitDataImport(importValidation.commit_token);
      setImportMessage(
        `インポート完了：追加${result.created}件、更新${result.updated}件、スキップ${result.skipped}件`,
      );
      setImportValidation(null);
      await load();
    } catch (error) {
      setActionError(error.message);
    } finally {
      setImporting(false);
    }
  }

  async function handleStorageValidation(event) {
    event.preventDefault();
    setStorageBusy(true);
    setActionError("");
    setStorageMessage("");
    try {
      setStoragePreview(
        await validateImageStorageTarget(storagePath.trim()),
      );
    } catch (error) {
      setActionError(error.message);
    } finally {
      setStorageBusy(false);
    }
  }

  async function handleStorageMigration() {
    if (
      !storagePreview?.ready ||
      storagePreview.same_path ||
      !window.confirm(
        "新しい保存先へ画像をコピーして設定を切り替えますか？旧保存先は削除されません。",
      )
    )
      return;
    setStorageBusy(true);
    setActionError("");
    try {
      const result = await migrateImageStorage(storagePreview.target_path);
      setStoragePreview(result);
      if (result.ready) {
        setStorageMessage(
          "画像保存先を切り替えました。旧保存先はそのまま残っています。",
        );
        setStoragePath("");
        await load();
      }
    } catch (error) {
      setActionError(error.message);
    } finally {
      setStorageBusy(false);
    }
  }

  return (
    <section className="page page--wide">
      <div className="page-heading">
        <div>
          <p className="eyebrow">System and data</p>
          <h1>SETTING</h1>
        </div>
        <button className="button" onClick={load} type="button">
          状態を更新
        </button>
      </div>
      {status === "loading" && <div className="message-panel">確認中…</div>}
      {status === "error" && (
        <div className="message-panel message-panel--error">
          システム状態を取得できませんでした。
        </div>
      )}
      {status === "ready" && (
        <>
          <section className="settings-section">
            <h2>システム状態</h2>
            <dl className="settings-status">
              <StatusItem label="アプリバージョン">
                v{system.version}
              </StatusItem>
              <StatusItem label="データベース">
                <span className="status-badge status-badge--ok">接続済み</span>
              </StatusItem>
              <StatusItem label="画像ストレージ">
                <span
                  className={
                    system.image_storage.writable
                      ? "status-badge status-badge--ok"
                      : "status-badge status-badge--error"
                  }
                >
                  {system.image_storage.writable
                    ? "書き込み可能"
                    : "書き込み不可"}
                </span>
              </StatusItem>
            </dl>
          </section>
          <section className="settings-section">
            <div className="section-heading">
              <div>
                <h2>画像保存先</h2>
                <p>アプリが管理する複製画像の保存場所です。</p>
              </div>
            </div>
            <code className="storage-path">{system.image_storage.path}</code>
            <dl className="settings-status settings-status--storage">
              <StatusItem label="画像使用量">
                {formatBytes(system.image_storage.used_bytes)}
              </StatusItem>
              <StatusItem label="ドライブ空き容量">
                {formatBytes(system.image_storage.free_bytes)}
              </StatusItem>
              <StatusItem label="利用中の画像">
                {system.image_storage.active_image_count}件
              </StatusItem>
              <StatusItem label="アーカイブ画像">
                {system.image_storage.archived_image_count}件
              </StatusItem>
            </dl>
            <form
              className="storage-migration"
              onSubmit={handleStorageValidation}
            >
              <label>
                新しい画像保存先
                <input
                  disabled={storageBusy}
                  onChange={(event) => {
                    setStoragePath(event.target.value);
                    setStoragePreview(null);
                    setStorageMessage("");
                  }}
                  placeholder="例: D:\PegmatiteImages"
                  required
                  value={storagePath}
                />
              </label>
              <button
                className="button"
                disabled={storageBusy}
                type="submit"
              >
                {storageBusy ? "確認中…" : "保存先を検証"}
              </button>
            </form>
            {storageMessage && (
              <div className="message-panel">{storageMessage}</div>
            )}
            {storagePreview && (
              <div className="storage-preview">
                <p>
                  コピー対象：{storagePreview.file_count}ファイル（
                  {formatBytes(storagePreview.total_bytes)}）
                </p>
                <p>
                  移行先空き容量：
                  {formatBytes(storagePreview.free_bytes)}
                </p>
                <code>{storagePreview.target_path}</code>
                {storagePreview.issues.length > 0 && (
                  <ul className="import-issues">
                    {storagePreview.issues.map((issue) => (
                      <li key={issue}>{issue}</li>
                    ))}
                  </ul>
                )}
                {storagePreview.ready && !storagePreview.same_path && (
                  <button
                    className="button button--primary"
                    disabled={storageBusy}
                    onClick={handleStorageMigration}
                    type="button"
                  >
                    コピー・照合して切り替える
                  </button>
                )}
                {storagePreview.same_path && (
                  <p className="status-badge status-badge--ok">
                    現在の保存先と同じです。
                  </p>
                )}
              </div>
            )}
          </section>
          <section className="settings-section">
            <h2>データ管理</h2>
            <p className="field-help">
              CSV出力には画像ファイル本体を含みません。画像は保存先と一緒にバックアップしてください。
            </p>
            {actionError && <div className="form-error">{actionError}</div>}
            {importMessage && (
              <div className="message-panel">{importMessage}</div>
            )}
            <div className="settings-actions">
              <button
                className="button button--primary"
                disabled={exporting}
                onClick={handleExport}
                type="button"
              >
                {exporting ? "CSV作成中…" : "CSV出力"}
              </button>
              <label className="button">
                {importing ? "処理中…" : "CSV取込"}
                <input
                  accept=".zip,application/zip"
                  className="visually-hidden"
                  disabled={importing}
                  onChange={handleImportFile}
                  type="file"
                />
              </label>
              <button className="button" disabled type="button">
                バックアップ
              </button>
              <Link className="button" to="/settings/archived-images">
                アーカイブ画像を管理
              </Link>
            </div>
            {importValidation && (
              <div className="import-preview">
                <h3>インポート事前検証</h3>
                <p>
                  追加 {importValidation.preview.created}件／更新{" "}
                  {importValidation.preview.updated}件／スキップ{" "}
                  {importValidation.preview.skipped}件
                </p>
                {importValidation.valid ? (
                  <>
                    <p className="status-badge status-badge--ok">
                      インポート可能です。画像メタデータはスキップされます。
                    </p>
                    <button
                      className="button button--primary"
                      disabled={importing}
                      onClick={handleImportCommit}
                      type="button"
                    >
                      この内容で確定
                    </button>
                  </>
                ) : (
                  <>
                    <p className="status-badge status-badge--error">
                      修正が必要です。
                    </p>
                    <ul className="import-issues">
                      {importValidation.issues.slice(0, 20).map((issue, index) => (
                        <li key={`${issue.file}-${issue.row}-${index}`}>
                          {issue.file} {issue.row}行目
                          {issue.field ? `（${issue.field}）` : ""}：
                          {issue.message}
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            )}
          </section>
        </>
      )}
    </section>
  );
}
