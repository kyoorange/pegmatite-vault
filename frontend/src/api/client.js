const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Accept: "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const error = new Error(
      payload?.error?.message ?? "APIリクエストに失敗しました。",
    );
    error.code = payload?.error?.code ?? "request_failed";
    error.status = response.status;
    error.details = payload?.error?.details ?? null;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export function getHealth(options = {}) {
  return apiRequest("/health", options);
}

export function getSystemStatus() {
  return apiRequest("/settings/status");
}

export function validateImageStorageTarget(path) {
  return jsonRequest("/settings/storage/validate", "POST", { path });
}

export function migrateImageStorage(path) {
  return jsonRequest("/settings/storage/migrate", "POST", { path });
}

export async function exportData() {
  const response = await fetch(`${API_BASE_URL}/data/export`, {
    method: "POST",
    headers: { Accept: "application/zip" },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(
      payload?.error?.message ?? "CSVエクスポートに失敗しました。",
    );
  }
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const filename =
    disposition.match(/filename="([^"]+)"/)?.[1] ??
    "pegmatite-vault-export.zip";
  return { blob: await response.blob(), filename };
}

export function validateDataImport(file) {
  const body = new FormData();
  body.append("file", file);
  return apiRequest("/data/import/validate", { method: "POST", body });
}

export function commitDataImport(commitToken) {
  return jsonRequest("/data/import/commit", "POST", {
    commit_token: commitToken,
  });
}

export function listSpecimens(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) {
      query.set(key, String(value));
    }
  });
  return apiRequest(`/specimens?${query}`);
}

export function getSpecimen(id) {
  return apiRequest(`/specimens/${id}`);
}

export function listMinerals(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) {
      query.set(key, String(value));
    }
  });
  return apiRequest(`/minerals?${query}`);
}

export function getMineral(id) {
  return apiRequest(`/minerals/${id}`);
}

export function createMineral(payload) {
  return jsonRequest("/minerals", "POST", payload);
}

export function updateMineral(id, payload) {
  return jsonRequest(`/minerals/${id}`, "PUT", payload);
}

export function deleteMineral(id) {
  return apiRequest(`/minerals/${id}`, { method: "DELETE" });
}

export function listMineralSpecimens(id, params = {}) {
  const query = new URLSearchParams(params);
  return apiRequest(`/minerals/${id}/specimens?${query}`);
}

export function getLocality(id) {
  return apiRequest(`/localities/${id}`);
}

export function listLocalities(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) {
      query.set(key, String(value));
    }
  });
  return apiRequest(`/localities?${query}`);
}

export function createLocality(payload) {
  return jsonRequest("/localities", "POST", payload);
}

export function updateLocality(id, payload) {
  return jsonRequest(`/localities/${id}`, "PUT", payload);
}

export function deleteLocality(id) {
  return apiRequest(`/localities/${id}`, { method: "DELETE" });
}

export function listLocalitySpecimens(id, params = {}) {
  const query = new URLSearchParams(params);
  return apiRequest(`/localities/${id}/specimens?${query}`);
}

export function getMineralClassOptions() {
  return apiRequest("/options/mineral-classes");
}

export function listNamedMasters(resource) {
  return apiRequest(`/${resource}`);
}

export function getNamedMaster(resource, id) {
  return apiRequest(`/${resource}/${id}`);
}

export function createNamedMaster(resource, payload) {
  return jsonRequest(`/${resource}`, "POST", payload);
}

export function updateNamedMaster(resource, id, payload) {
  return jsonRequest(`/${resource}/${id}`, "PUT", payload);
}

export function deleteNamedMaster(resource, id) {
  return apiRequest(`/${resource}/${id}`, { method: "DELETE" });
}

function jsonRequest(path, method, payload) {
  return apiRequest(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function createSpecimen(payload) {
  return jsonRequest("/specimens", "POST", payload);
}

export function updateSpecimen(id, payload) {
  return jsonRequest(`/specimens/${id}`, "PATCH", payload);
}

export function deleteSpecimen(id) {
  return apiRequest(`/specimens/${id}`, { method: "DELETE" });
}

export function imageContentUrl(id, variant = "thumbnail") {
  const query = new URLSearchParams({ variant });
  return `${API_BASE_URL}/images/${id}/content?${query}`;
}

export function archivedImageContentUrl(id, variant = "thumbnail") {
  const query = new URLSearchParams({ variant });
  return `${API_BASE_URL}/archived-images/${id}/content?${query}`;
}

export function listArchivedImages(params = {}) {
  const query = new URLSearchParams(params);
  return apiRequest(`/archived-images?${query}`);
}

export function restoreImage(imageId, specimenId) {
  return jsonRequest(`/images/${imageId}/restore`, "POST", {
    specimen_id: specimenId,
  });
}

export function permanentlyDeleteImage(imageId) {
  return apiRequest(`/images/${imageId}/permanent`, { method: "DELETE" });
}

export function uploadSpecimenImage(specimenId, file, caption = "") {
  const body = new FormData();
  body.append("file", file);
  if (caption) {
    body.append("caption", caption);
  }
  return apiRequest(`/specimens/${specimenId}/images`, {
    method: "POST",
    body,
  });
}

export function reorderSpecimenImages(specimenId, imageIds) {
  return jsonRequest(`/specimens/${specimenId}/images/order`, "PATCH", {
    image_ids: imageIds,
  });
}

export function archiveImage(imageId) {
  return apiRequest(`/images/${imageId}`, { method: "DELETE" });
}

export function getSpecimenOptions() {
  return Promise.all([
    apiRequest("/options/minerals"),
    apiRequest("/options/localities"),
    apiRequest("/options/acquisition-methods"),
  ]).then(([minerals, localities, acquisitionMethods]) => ({
    minerals,
    localities,
    acquisitionMethods,
  }));
}
