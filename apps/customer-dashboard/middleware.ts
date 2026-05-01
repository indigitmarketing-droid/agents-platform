import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function middleware(req: NextRequest) {
  const res = NextResponse.next();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => req.cookies.getAll(),
        setAll: (list: { name: string; value: string; options: CookieOptions }[]) =>
          list.forEach(({ name, value, options }) =>
            res.cookies.set(name, value, options),
          ),
      },
    },
  );

  const { data: { user } } = await supabase.auth.getUser();
  const path = req.nextUrl.pathname;

  // Public routes (no auth required)
  const publicPaths = ["/login", "/forgot-password", "/reset-password"];
  if (
    publicPaths.some((p) => path.startsWith(p)) ||
    path.startsWith("/api/auth")
  ) {
    return res;
  }

  // Protected: must be authenticated
  if (!user) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  // Force password change on first login
  const passwordChanged = user.user_metadata?.password_changed === true;
  if (!passwordChanged && path !== "/change-password") {
    return NextResponse.redirect(new URL("/change-password", req.url));
  }

  return res;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
