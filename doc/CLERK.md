# Clerk Authentication Configuration

Chalksmith uses Clerk for account creation, sign-in, session management, and account settings. The browser obtains a short-lived Clerk session JWT and sends it directly to FastAPI as `Authorization: Bearer <token>`. FastAPI verifies the JWT signature through the Clerk JWKS endpoint and uses its `sub` claim as the lesson `owner_id`.

Use the same Clerk application as Chalksmith v1 whenever possible. Reusing that application preserves existing `user_...` IDs and therefore preserves ownership of migrated lessons without an account-remapping table.

## 1. Configure the Clerk environments

There is no single Clerk Dashboard field where a normal web application should
enter local, production, and Cloud Run URLs. Development and Production are
separate Clerk instances and have different domain rules.

### 1.1 Local development

1. Open the [Clerk Dashboard](https://dashboard.clerk.com/) and select the
   Chalksmith application used by v1, or create an application if no reusable
   one exists.
2. In the instance selector at the top, select **Development**.
3. Under **User & Authentication**, enable the sign-in methods Chalksmith should
   offer. Email/password and Google are sufficient for local testing; enable
   Microsoft only when its OAuth credentials are ready.
4. Open **API keys** and use the Development `pk_test_...` and `sk_test_...`
   values in `.env/clerk.key.stg` as shown in [Section 3](#3-configure-localstaging-development).

Do not add `http://localhost:3000` to a production domain setting. Clerk's
Development instance accepts localhost applications; the exact local browser
origin is restricted by Chalksmith's effective authorized parties, which inherit
`FRONTEND_ORIGINS` unless explicitly overridden.

### 1.2 Production domain

The production primary domain must be the bare root domain exported as `DOMAIN`
when Chalksmith is deployed. For example, use `chalksmith.ai`, not
`https://chalksmith.ai`, `www.chalksmith.ai`, or `app.chalksmith.ai`.

1. At the top of Clerk Dashboard, open the **Development** instance selector and
   select **Create production instance**. Choose whether to clone the Development
   settings. If a Production instance already exists, select it instead.
2. Enter the root domain when prompted. If the instance already exists, open
   **Domains** and configure that domain as the primary domain.
3. On **Domains**, open the primary domain and copy every DNS record shown under
   **DNS configuration** into the authoritative DNS provider. These Clerk records
   are separate from the Cloud Run records in [DOMAIN.md](DOMAIN.md); both sets
   are required and records for one service must not replace records for the
   other.
4. Wait until Clerk shows the DNS records as verified. If Cloudflare hosts DNS,
   keep Clerk CNAME records in **DNS only** mode while they are validated.
5. Return to the Production instance home page and select **Deploy certificates**
   when Clerk makes the button available.
6. Open **API keys** while the Production instance is selected and copy the new
   `pk_live_...`, `sk_live_...`, and Frontend API URL values for
   [Section 4](#4-configure-production-deployment).
7. Configure production OAuth credentials for each enabled social provider;
   Clerk's shared Development OAuth credentials are not used in Production.

One primary root domain covers the current `chalksmith.ai`, `www.chalksmith.ai`,
and `app.chalksmith.ai` layout, and Clerk shares sessions across those subdomains.
Use the subdomain allowlist on the primary domain to restrict access to the exact
subdomains Chalksmith uses.

Do not try to add the generated `*.run.app` Cloud Run hostname to Clerk. Clerk
production keys work only on the configured production domain. The `run.app`
URL remains useful for unauthenticated deployment diagnostics such as
`curl -I`, but not for testing production sign-in. Two unrelated base domains
require Clerk satellite-domain configuration as described in
[DOMAIN.md](DOMAIN.md#42-serve-the-complete-application-on-both-domains).

Before public launch, also configure the age and legal-consent fields in the
Clerk sign-up flow.

The current frontend uses Clerk's hosted modal components. Provider callbacks, password reset, account linking, session renewal, and account management are handled by Clerk rather than custom application forms.

## 2. Copy the application values

Open **Clerk Dashboard -> API keys** for the currently selected instance and
collect:

| Clerk value | Application variable | Exposure |
| :--- | :--- | :--- |
| Publishable key | `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Public browser configuration |
| Secret key | `CLERK_SECRET_KEY` | Server secret; never commit or expose to the browser |
| Frontend API URL / token issuer | `CLERK_ISSUER` | Non-secret backend verification setting |

Copy the exact Frontend API URL shown for the selected instance and omit a
trailing slash. Development normally uses
`https://<instance>.clerk.accounts.dev`; after production DNS is configured,
Production normally uses `https://clerk.<your-domain>`. This exact URL is
`CLERK_ISSUER` because it is the issuer of Clerk's session JWTs.

`CLERK_JWKS_URL` is optional. When empty, FastAPI uses `<CLERK_ISSUER>/.well-known/jwks.json`. `CLERK_AUDIENCE` is also optional and should only be set when the Clerk session-token configuration emits a matching `aud` claim.

## 3. Configure local/staging development

Local configuration lives in the ignored root `.env/` directory.

Create the local/staging file from the shared template and restrict its file
permissions:

```bash
cp bin/clerk.key.template .env/clerk.key.stg
chmod 600 .env/clerk.key.stg
```

Use values from the Clerk **Development** instance. The completed file contains:

```dotenv
CLERK_ISSUER=https://<instance>.clerk.accounts.dev
CLERK_JWKS_URL=
CLERK_AUDIENCE=
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

Do not add `CLERK_AUTHORIZED_PARTIES`. The rest of the local configuration,
including `FRONTEND_ORIGINS=http://localhost:3000` and `NEXT_PUBLIC_API_URL`,
lives in `.env/env.local`. The backend uses `FRONTEND_ORIGINS` as the authorized
parties when no explicit override exists. Restart both Next.js and FastAPI after
changing either file. The frontend loads them through `frontend/next.config.ts`;
the backend through `backend/app/core/config.py`. `bin/setup.sh stg` reads
`CLERK_SECRET_KEY` from this same file.

## 4. Configure production deployment

Complete the Production domain, DNS, and certificate steps in
[Section 1.2](#12-production-domain), then create the production file from the
same template:

```bash
cp bin/clerk.key.template .env/clerk.key.prod
chmod 600 .env/clerk.key.prod
```

Use values from the Clerk **Production** instance. The completed ignored file
contains:

```dotenv
CLERK_ISSUER=https://clerk.example.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
```

Replace `example.com` and all placeholder values with the exact Production
values shown by Clerk. Do not add `CLERK_AUTHORIZED_PARTIES` and do not commit
this file. `deploy.sh` derives the production authorized parties from `DOMAIN`
and injects them directly into the API service alongside `FRONTEND_ORIGINS`.

`bin/setup.sh prod start` reads `CLERK_SECRET_KEY` from this file when it creates
the `chalksmith-clerk-key-prod` Secret Manager secret. `bin/deploy.sh prod start`
reads `CLERK_ISSUER` and `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` from the same file,
compiles the publishable key into the web image, and mounts only the secret key
into the Next.js Cloud Run service at runtime.

```bash
cp bin/env.deploy.template .env/env.deploy
chmod 600 .env/env.deploy

# Replace its placeholders before running these commands. setup.sh still reads
# PROJECT_ID from the shell; deploy.sh reads the file automatically.
export PROJECT_ID=your-project-id

./bin/setup.sh prod start
./bin/deploy.sh prod start
```

If the production Clerk secret is rotated after the Secret Manager secret
already has a version, add the new `sk_live_...` value as a new secret version;
`setup.sh` deliberately does not overwrite an existing secret:

```bash
gcloud secrets versions add chalksmith-clerk-key-prod \
  --project="$PROJECT_ID" \
  --data-file=-
```

Enter the new value on standard input and press Control-D. Redeploy the web
service afterward so its `latest` secret mount uses the current version.

Finally, create the Cloud Run Domain Mappings and product DNS records in
[DOMAIN.md](DOMAIN.md), then test sign-in through `https://example.com` or one of
its configured subdomains. Do not use the generated `run.app` URL for this test.

## 5. Existing-user and lesson ownership rules

- The backend stores only the Clerk JWT `sub` value on `lessons.owner_id`; it does not copy passwords or maintain a second user directory.
- Reusing the v1 Clerk application preserves existing owner IDs.
- If a different Clerk application must be used, prepare an explicit old-user-ID to new-user-ID JSON map and pass it to `backend/scripts/migrate_v1.py --owner-map`. Never merge accounts only because their email strings match.
- No account-sync Webhook is required unless a future product feature needs a local user profile table.

## 6. Verification

### 6.1 Local

1. Start the web, API, and renderer processes described in [README.md](../README.md).
2. Sign up or sign in at `http://localhost:3000`.
3. Generate a lesson and confirm the API does not return `401`.
4. Sign out and confirm generation and dashboard screens require sign-in.
5. Sign in as a second user and confirm the first user's lesson is not returned.

If sign-in works but API calls return `401`, verify that `CLERK_ISSUER` belongs
to the same application as the publishable/secret keys and that
`FRONTEND_ORIGINS` includes the browser's exact origin. Unless explicitly
overridden, that same list is used as `CLERK_AUTHORIZED_PARTIES`. A JWKS network
failure returns `503`, while an expired, malformed, wrongly issued, or
disallowed-origin token returns `401`.

### 6.2 Production

1. In Clerk Dashboard, select **Production -> Domains** and confirm the primary
   domain and its DNS records show as verified.
2. Confirm the Production home page no longer asks to deploy certificates.
3. Open `https://example.com` and `https://app.example.com`, replacing the sample
   domain with `DOMAIN`, and complete sign-in on both hosts.
4. Generate and reopen a lesson to verify that the session token is accepted by
   FastAPI.
5. Use the generated `run.app` URL only with `curl -I`; do not use a Clerk origin
   error on that URL as evidence that the custom-domain deployment failed.

## References

- [Clerk Next.js quickstart](https://clerk.com/docs/nextjs/getting-started/quickstart)
- [Deploy a Clerk app to production](https://clerk.com/docs/guides/development/deployment/production)
- [Clerk instances and environments](https://clerk.com/docs/guides/development/managing-environments)
- [Clerk session tokens](https://clerk.com/docs/guides/sessions/session-tokens)
- [Manual JWT verification](https://clerk.com/docs/guides/sessions/manual-jwt-verification)
