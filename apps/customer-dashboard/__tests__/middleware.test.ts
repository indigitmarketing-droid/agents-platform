import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@supabase/ssr", () => ({
  createServerClient: vi.fn(),
}));

import { middleware } from "../middleware";
import { createServerClient } from "@supabase/ssr";
import { NextRequest } from "next/server";

function makeReq(path: string) {
  return new NextRequest(`http://localhost:3000${path}`);
}

function mockSupabase(user: any) {
  (createServerClient as any).mockReturnValue({
    auth: {
      getUser: vi.fn().mockResolvedValue({ data: { user } }),
    },
  });
}

describe("middleware", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://test.supabase.co";
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "anon";
  });

  it("allows /login without auth", async () => {
    mockSupabase(null);
    const res = await middleware(makeReq("/login"));
    expect(res.status).toBe(200);
  });

  it("allows /forgot-password without auth", async () => {
    mockSupabase(null);
    const res = await middleware(makeReq("/forgot-password"));
    expect(res.status).toBe(200);
  });

  it("redirects unauthenticated user to /login", async () => {
    mockSupabase(null);
    const res = await middleware(makeReq("/"));
    expect(res.status).toBe(307);
    expect(res.headers.get("location")).toContain("/login");
  });

  it("redirects user with password_changed=false to /change-password", async () => {
    mockSupabase({ id: "uid", user_metadata: { password_changed: false } });
    const res = await middleware(makeReq("/"));
    expect(res.status).toBe(307);
    expect(res.headers.get("location")).toContain("/change-password");
  });

  it("allows authenticated user with password_changed=true to access /", async () => {
    mockSupabase({ id: "uid", user_metadata: { password_changed: true } });
    const res = await middleware(makeReq("/"));
    expect(res.status).toBe(200);
  });

  it("allows /change-password access for user without password_changed flag (no redirect loop)", async () => {
    mockSupabase({ id: "uid", user_metadata: { password_changed: false } });
    const res = await middleware(makeReq("/change-password"));
    expect(res.status).toBe(200);
  });
});
