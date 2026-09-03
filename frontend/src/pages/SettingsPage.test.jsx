import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";

import SettingsPage from "./SettingsPage";

afterEach(() => {
  vi.restoreAllMocks();
});

it("shows database and image storage status", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({
      version: "0.1.0",
      database: "ok",
      image_storage: {
        path: "D:\\PegmatiteImages",
        writable: true,
        used_bytes: 1024,
        free_bytes: 1024 * 1024,
        active_image_count: 2,
        archived_image_count: 1,
      },
    }),
  });

  render(
    <MemoryRouter>
      <SettingsPage />
    </MemoryRouter>,
  );

  expect(
    await screen.findByText("D:\\PegmatiteImages"),
  ).toBeInTheDocument();
  expect(screen.getByText("接続済み")).toBeInTheDocument();
  expect(screen.getByText("書き込み可能")).toBeInTheDocument();
  expect(screen.getByText("2件")).toBeInTheDocument();
  expect(screen.getByText("1件")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "CSV出力" })).toBeEnabled();
});
