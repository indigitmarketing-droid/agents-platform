import { NextResponse, type NextRequest } from "next/server";

const ADMIN_USER = process.env.ADMIN_USERNAME;
const ADMIN_PASS = process.env.ADMIN_PASSWORD;
const REALM = "Agents Operator Dashboard";

function unauthorized() {
  return new NextResponse("Unauthorized", {
    status: 401,
    headers: { "WWW-Authenticate": `Basic realm="${REALM}"` },
  });
}

export function middleware(req: NextRequest) {
  const path = req.nextUrl.pathname;

  // Webhooks have their own HMAC verification — must remain reachable without browser auth
  if (path.startsWith("/api/webhooks/")) {
    return NextResponse.next();
  }

  if (!ADMIN_USER || !ADMIN_PASS) {
    return new NextResponse("Auth not configured (missing ADMIN_USERNAME/ADMIN_PASSWORD env)", { status: 503 });
  }

  const auth = req.headers.get("authorization");
  if (!auth?.startsWith("Basic ")) {
    return unauthorized();
  }

  let user: string | undefined;
  let pass: string | undefined;
  try {
    const decoded = atob(auth.slice(6));
    const sep = decoded.indexOf(":");
    user = sep >= 0 ? decoded.slice(0, sep) : decoded;
    pass = sep >= 0 ? decoded.slice(sep + 1) : "";
  } catch {
    return unauthorized();
  }

  if (user !== ADMIN_USER || pass !== ADMIN_PASS) {
    return unauthorized();
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
