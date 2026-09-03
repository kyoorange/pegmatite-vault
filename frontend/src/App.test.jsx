import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("renders the home route", () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("offline"));

    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "HOME" })).toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: "＋ 標本を追加" })[0],
    ).toHaveAttribute("href", "/specimens/new");
  });
});
