# Clerk Authentication Configuration

Chalksmith uses Clerk for account creation, sign-in, session management, and account settings. The browser obtains a short-lived Clerk session JWT and sends it directly to FastAPI as `Authorization: Bearer <token>`. FastAPI verifies the JWT signature through the Clerk JWKS endpoint and uses its `sub` claim as the lesson `owner_id`.

Use the same Clerk application as Chalksmith v1 whenever possible. Reusing that application preserves existing `user_...` IDs and therefore preserves ownership of migrated lessons without an account-remapping table.

## 1. Configure the Clerk application

1. Open the [Clerk Dashboard](https://dashboard.clerk.com/) and select the Chalksmith application used by v1, or create an application if no reusable one exists.
2. Under **User & Authentication**, enable the sign-in methods Chalksmith should offer. Email/password and Google are sufficient for local testing; enable Microsoft only when its OAuth credentials and redirect URLs are ready.
3. Add local and production application URLs in the Clerk dashboard:
   - `http://localhost:3000`
   - `https://chalksmith.ai`
   - `https://www.chalksmith.ai`
   - `https://app.chalksmith.ai`
   - the generated Cloud Run web URL after the first deployment
4. Configure production DNS in Clerk if Chalksmith uses a custom authentication domain or Clerk's multi-domain/satellite support.
5. Configure the age and legal-consent fields in the Clerk sign-up flow before public launch.

The current frontend uses Clerk's hosted modal components. Provider callbacks, password reset, account linking, session renewal, and account management are handled by Clerk rather than custom application forms.

## 2. Copy the application values

Open **Clerk Dashboard → Configure → API keys** and collect:

| Clerk value | Application variable | Exposure |
| :--- | :--- | :--- |
| Publishable key | `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Public browser configuration |
| Secret key | `CLERK_SECRET_KEY` | Server secret; never commit or expose to the browser |
| Frontend API URL / token issuer | `CLERK_ISSUER` | Non-secret backend verification setting |

The issuer normally resembles `https://<instance>.clerk.accounts.dev`. Copy the exact Frontend API URL shown for the selected Clerk instance and omit a trailing slash.

`CLERK_JWKS_URL` is optional. When empty, FastAPI uses `<CLERK_ISSUER>/.well-known/jwks.json`. `CLERK_AUDIENCE` is also optional and should only be set when the Clerk session-token configuration emits a matching `aud` claim.

## 3. Configure local development

Local configuration lives in the ignored root `.env/` directory.

`.env/.env.frontend.local`:

```dotenv
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

`.env/.env.backend.local`:

```dotenv
CLERK_ISSUER=https://<instance>.clerk.accounts.dev
CLERK_JWKS_URL=
CLERK_AUDIENCE=
CLERK_AUTHORIZED_PARTIES=http://localhost:3000
```

Restart both Next.js and FastAPI after changing these values. The frontend reads its file through `frontend/next.config.ts`; the backend reads its file through `backend/app/core/config.py`.

## 4. Configure production deployment

The publishable key is compiled into the web image. Store the secret key in Google Secret Manager so the Next.js Cloud Run service receives it only at runtime:

```bash
gcloud secrets create chalksmith-clerk-secret-key \
  --project=your-project-id \
  --replication-policy=automatic
gcloud secrets versions add chalksmith-clerk-secret-key \
  --project=your-project-id \
  --data-file=-
```

Enter the `sk_live_...` value on standard input, then press Control-D. Do not place it in a tracked shell script.

Before running `infra/gcloud/deploy.sh`, export:

```bash
export CLERK_PUBLISHABLE_KEY=pk_live_...
export CLERK_SECRET_KEY_SECRET_NAME=chalksmith-clerk-secret-key
export CLERK_ISSUER=https://<production-instance>.clerk.accounts.dev
```

The deploy script creates a dedicated `chalksmith-web` service account, grants only that account access to the Clerk secret, passes the publishable key at build time, and configures the API with the issuer and authorized browser origins.

## 5. Existing-user and lesson ownership rules

- The backend stores only the Clerk JWT `sub` value on `lessons.owner_id`; it does not copy passwords or maintain a second user directory.
- Reusing the v1 Clerk application preserves existing owner IDs.
- If a different Clerk application must be used, prepare an explicit old-user-ID to new-user-ID JSON map and pass it to `backend/scripts/migrate_v1.py --owner-map`. Never merge accounts only because their email strings match.
- No account-sync Webhook is required unless a future product feature needs a local user profile table.

## 6. Verification

1. Start the web, API, and renderer processes described in [README.md](README.md).
2. Sign up or sign in at `http://localhost:3000`.
3. Generate a lesson and confirm the API does not return `401`.
4. Sign out and confirm generation and dashboard screens require sign-in.
5. Sign in as a second user and confirm the first user's lesson is not returned.

If sign-in works but API calls return `401`, verify that `CLERK_ISSUER` belongs to the same application as the publishable/secret keys and that `CLERK_AUTHORIZED_PARTIES` includes the browser's exact origin. A JWKS network failure returns `503`, while an expired, malformed, wrongly issued, or disallowed-origin token returns `401`.

## References

- [Clerk Next.js quickstart](https://clerk.com/docs/nextjs/getting-started/quickstart)
- [Clerk session tokens](https://clerk.com/docs/guides/sessions/session-tokens)
- [Manual JWT verification](https://clerk.com/docs/guides/sessions/manual-jwt-verification)
