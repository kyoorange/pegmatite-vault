export default function PlaceholderPage({ title, description }) {
  return (
    <section className="page">
      <p className="eyebrow">Pegmatite Vault</p>
      <h1>{title}</h1>
      <p className="page-description">{description}</p>
      <div className="empty-state">
        <p>基盤の準備ができました。</p>
        <small>この領域は次の実装フェーズで完成させます。</small>
      </div>
    </section>
  );
}
