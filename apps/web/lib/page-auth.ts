import { ApiError, clearTokens, hasAccessToken } from "@/lib/api-client";

type RouterLike = {
  replace: (href: string) => void;
};

export function requireAuthOrRedirect(router: RouterLike): boolean {
  if (!hasAccessToken()) {
    router.replace("/login");
    return false;
  }
  return true;
}

export function handlePageApiError(error: unknown, router: RouterLike): string {
  if (error instanceof ApiError && error.status === 401) {
    clearTokens();
    router.replace("/login");
    return "Сесс дууссан тул дахин нэвтэрнэ үү.";
  }
  if (error instanceof ApiError) {
    return error.detail;
  }
  return "Өгөгдөл ачаалах үед алдаа гарлаа.";
}
