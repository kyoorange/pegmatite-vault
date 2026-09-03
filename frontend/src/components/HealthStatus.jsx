import { useEffect, useState } from "react";

import { getHealth } from "../api/client";

export default function HealthStatus() {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    const controller = new AbortController();

    getHealth({ signal: controller.signal })
      .then(() => setStatus("ok"))
      .catch(() => setStatus("unavailable"));

    return () => controller.abort();
  }, []);

  const labels = {
    checking: "接続確認中",
    ok: "API接続済み",
    unavailable: "API未接続",
  };

  return <span className={`health health--${status}`}>{labels[status]}</span>;
}
