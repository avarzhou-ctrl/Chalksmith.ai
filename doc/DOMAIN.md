# Custom Domain Configuration

Chalksmith deploys its web, API, and renderer services to Cloud Run. Only the
web service is exposed through the product domain; the browser calls the API URL
compiled into the web image, and lesson artifacts continue to load from private
GCS objects through signed URLs.

This guide covers the current no-load-balancer setup using Cloud Run Domain
Mapping. Google currently labels direct Cloud Run domain mapping as Beta and
recommends a global external Application Load Balancer for production workloads.
It is nevertheless the simplest front door for a small single-region deployment
in a supported region such as `us-central1`.

## 1. What `deploy.sh` configures

Production deployment reads one bare base domain from `.env/env.deploy`:

```bash
cp bin/env.deploy.template .env/env.deploy
chmod 600 .env/env.deploy

# Replace its placeholders, including DOMAIN=example.com, then run directly:
./bin/deploy.sh prod start
```

Do not include `https://`, a path, port, trailing comma, or multiple domains in
`DOMAIN`.

For `DOMAIN=example.com`, `bin/deploy.sh` configures these application origins:

| Host | Current application role |
| :--- | :--- |
| `example.com` | Marketing site |
| `www.example.com` | Marketing site |
| `app.example.com` | Generation and Dashboard application |

The script adds all three HTTPS origins to the API's CORS and Clerk authorized
parties, compiles `example.com` into the Next.js host-routing rules, and adds the
generated Cloud Run web URL as an allowed backend origin.

The script does **not**:

- verify ownership of the domain;
- create Cloud Run Domain Mapping resources;
- add or change DNS records;
- create a load balancer or static IP address;
- configure the production domain and DNS records required by Clerk.

Domain mappings and DNS records have a longer lifecycle than Cloud Run revisions,
so they should not be recreated by every application deployment.

## 2. Prerequisites

Before mapping a domain:

1. Deploy production successfully and note the printed web service name and URL.
   The default service is `chalksmith-web-prod`.
2. Confirm the base domain is registered and that its DNS records can be edited.
3. Use a Google account that can manage the Cloud Run service and verify domain
   ownership. Domain ownership is verified outside IAM through Google Search
   Console.
4. Confirm the Cloud Run region supports direct Domain Mapping. `us-central1`
   is supported.
5. Configure a Clerk production instance with `pk_live_...` and `sk_live_...`
   credentials as described in [CLERK.md](CLERK.md).

Verify each independently owned base domain once:

```bash
gcloud domains verify example.com
```

Complete the Search Console flow opened by the command. Verifying
`example.com` also proves ownership for `www.example.com` and
`app.example.com`.

## 3. Map one base domain

Set the deployment identifiers:

```bash
export PROJECT_ID=your-project-id
export REGION=us-central1
export WEB_SERVICE=chalksmith-web-prod
export DOMAIN=example.com
```

Create one mapping for every hostname that users will visit. The following loop
is safe to rerun because it skips mappings that already exist:

```bash
for host in "$DOMAIN" "www.$DOMAIN" "app.$DOMAIN"; do
  if gcloud beta run domain-mappings describe \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --domain="$host" >/dev/null 2>&1; then
    echo "exists: $host"
  else
    gcloud beta run domain-mappings create \
      --project="$PROJECT_ID" \
      --region="$REGION" \
      --service="$WEB_SERVICE" \
      --domain="$host"
  fi
done
```

If a hostname is already mapped to a different Cloud Run service, investigate
that mapping before changing it. Use `--force-override` only when moving that
hostname is intentional.

### 3.1 Retrieve the required DNS records

Cloud Run generates the records, but it cannot add them at the registrar or DNS
provider:

```bash
for host in "$DOMAIN" "www.$DOMAIN" "app.$DOMAIN"; do
  echo "=== $host ==="
  gcloud beta run domain-mappings describe \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --domain="$host" \
    --format="yaml(status.resourceRecords,status.conditions)"
done
```

Add **every** record shown under `status.resourceRecords` to the authoritative DNS
provider. Cloud Run commonly returns `A` and `AAAA` records for the root domain
and `CNAME` records for subdomains, but the command output is the source of truth;
do not copy record values from another domain.

If the DNS zone is hosted in Cloud DNS, records can be added with
`gcloud dns record-sets create` or as a transaction. For example, after replacing
the placeholders with one returned record:

```bash
gcloud dns record-sets create app.example.com. \
  --project="$PROJECT_ID" \
  --zone=your-managed-zone \
  --type=CNAME \
  --ttl=300 \
  --rrdatas=returned-target.example.
```

For Cloudflare or another DNS provider, add the returned records there. Keep
Cloudflare records in **DNS only** mode while Cloud Run validates the mapping and
provisions its certificate; proxying or forced HTTPS can prevent validation and
certificate renewal.

### 3.2 Wait for DNS and HTTPS

DNS propagation and certificate issuance are asynchronous. Recheck the mapping:

```bash
gcloud beta run domain-mappings describe \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --domain="$DOMAIN" \
  --format="yaml(status.conditions)"
```

Then verify DNS and HTTPS from the client network:

```bash
dig +short example.com A
dig +short example.com AAAA
dig +short www.example.com CNAME
dig +short app.example.com CNAME

curl -I https://example.com
curl -I https://www.example.com
curl -I https://app.example.com
```

The managed certificate is requested automatically after the required DNS
records resolve. It often becomes available within minutes, but DNS propagation
and certificate issuance can take up to 24 hours.

## 4. Two different base domains

`example.com` and `another.com` are different base domains. The current
application accepts only one value in `DOMAIN`; this is invalid:

```bash
export DOMAIN=example.com,another.com
```

Deploying once with `DOMAIN=example.com` and again with `DOMAIN=another.com` is
also incorrect. The second deployment rebuilds the same web service and
overwrites the compiled host routing, CORS origins, and Clerk authorized parties
with the second domain.

Choose one of the following designs before mapping the second base domain.

### 4.1 Recommended: make the second domain an alias

Keep one canonical production domain and permanently redirect the second domain:

```text
another.com       -> example.com
www.another.com   -> www.example.com
app.another.com   -> app.example.com
```

This keeps Clerk, OAuth callbacks, passkeys, cookies, canonical URLs, and search
indexing on one domain.

DNS records cannot perform HTTP redirects. Use one of these approaches:

- configure an HTTPS redirect at the DNS/CDN provider;
- map the alias hostnames to `chalksmith-web-prod` and add host-based permanent
  redirects to the Next.js middleware;
- use a load-balancer URL redirect if an external Application Load Balancer is
  introduced later.

When Next.js performs the redirect, create Domain Mappings and DNS records for
the alias hostnames too, so Cloud Run can terminate HTTPS before returning the
redirect. The current repository does not yet implement a `DOMAIN_ALIASES`
variable or alias-host redirect rules.

### 4.2 Serve the complete application on both domains

Fully serving the same authenticated application on two unrelated base domains
requires application and Clerk changes in addition to six Domain Mappings and
their DNS records:

1. Compile both domain families into the Next.js host-routing configuration.
2. Add the root, `www`, and `app` origins for both domains to FastAPI CORS and
   Clerk authorized parties.
3. Choose one Clerk primary domain and configure the other as a Clerk satellite
   domain.
4. Configure Clerk's request-dependent `isSatellite`, `domain`, `signInUrl`,
   `signUpUrl`, and allowed redirect origins.
5. Add Clerk's separate DNS records for the satellite domain.
6. Test sign-in, sign-out, OAuth callbacks, session refresh, and cross-domain
   redirects on both domains.

Clerk satellite domains are an advanced feature, require a paid plan in
production, and are not recommended with passkeys. Do not point a second base
domain at the service and assume the existing production Clerk key will work
there without satellite configuration.

## 5. Clerk domain checklist

Cloud Run DNS records route product traffic; Clerk DNS records serve Clerk's
Frontend API and email/authentication infrastructure. They are separate record
sets and both must be configured.

For one base domain:

1. Set the production root domain in **Clerk Dashboard -> Domains**.
2. Add every DNS record requested by Clerk without replacing Cloud Run records
   of another type or hostname.
3. Deploy the Clerk-managed certificates.
4. Allow the production root, `www`, and `app` URLs.
5. Do not add the generated Cloud Run `run.app` URL as a production Clerk
   domain. Production keys work only on the configured custom domain; use the
   generated URL only for unauthenticated deployment diagnostics.
6. Verify that the API's `CLERK_AUTHORIZED_PARTIES` and `FRONTEND_ORIGINS` include
   the custom origins. `deploy.sh` performs this step for its single `DOMAIN`.

Clerk sessions are shared across subdomains of one configured root domain. That
is why `example.com` and `app.example.com` do not require satellite-domain mode.

## 6. Troubleshooting

### Domain mapping remains pending

- Run `domain-mappings describe` and add every returned resource record.
- Confirm the records exist at the authoritative nameservers, not only in a
  local DNS dashboard.
- Remove conflicting `A`, `AAAA`, or `CNAME` records for the same hostname only
  after confirming they are obsolete.
- Disable a CDN proxy until validation completes.
- Check that `CAA` records allow the certificate authority used by Google.
- Allow up to 24 hours after correcting DNS.

### Domain ownership or permission failure

- Run `gcloud domains verify BASE_DOMAIN` as the Google account creating the
  mapping.
- Confirm that account has permission to manage the target Cloud Run service.
- Verify the base domain rather than only one subdomain.

### Site opens but login or API calls fail

- Confirm production uses Clerk `pk_live_...` and `sk_live_...` keys.
- Confirm the custom URL is configured in the Clerk production instance.
- Check `FRONTEND_ORIGINS` and `CLERK_AUTHORIZED_PARTIES` on
  `chalksmith-api-prod`.
- Do not redeploy the same service with a different `DOMAIN`; the most recent
  build controls host routing.
- Inspect the browser console for CORS errors and Clerk origin-validation errors.

### Root domain works but `www` or `app` does not

Each hostname needs its own Domain Mapping and corresponding DNS records. A root
mapping does not automatically include `www` or `app`, and the managed
certificate does not implicitly cover unconfigured hostnames.

## 7. Lifecycle and removal

Normal `./bin/deploy.sh prod start` runs replace Cloud Run revisions without
requiring DNS changes. Treat mappings and DNS as persistent front-door
resources.

List mappings before making lifecycle changes:

```bash
gcloud beta run domain-mappings list \
  --project="$PROJECT_ID" \
  --region="$REGION"
```

To intentionally remove a hostname mapping:

```bash
gcloud beta run domain-mappings delete \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --domain=www.example.com
```

Delete or replace its DNS records separately. Do not remove a mapping or DNS
record during an ordinary application deployment.

## References

- [Cloud Run: Mapping custom domains](https://cloud.google.com/run/docs/mapping-custom-domains)
- [Cloud Run regions](https://cloud.google.com/run/docs/locations)
- [Cloud DNS: Add, update, and delete records](https://cloud.google.com/dns/docs/records)
- [Clerk production deployment](https://clerk.com/docs/guides/development/deployment/production)
- [Clerk authentication across different domains](https://clerk.com/docs/guides/dashboard/dns-domains/satellite-domains)
- [GCP deployment](GCP.md)
- [Clerk configuration](CLERK.md)
- [Cost model](COST.md)
