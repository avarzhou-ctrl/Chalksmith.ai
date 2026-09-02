const configuredDomain = process.env.NEXT_PUBLIC_SITE_DOMAIN;

// Production links cross hosts directly; local development stays on one origin.
export const homeHref = configuredDomain ? `https://${configuredDomain}/` : '/';
export const dashboardHref = configuredDomain ? `https://app.${configuredDomain}/home` : '/dashboard';
export const generationHref = configuredDomain ? `https://app.${configuredDomain}/generation` : '/generation';
