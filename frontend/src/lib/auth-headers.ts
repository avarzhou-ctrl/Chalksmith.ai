export const PROXY_AUTH_USER_ID_HEADER = 'x-chalksmith-auth-user-id';

export function getProxyAuthUserId(request: Request) {
  return request.headers.get(PROXY_AUTH_USER_ID_HEADER);
}
