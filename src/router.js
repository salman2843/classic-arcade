// Tiny hash router.
//
// Routes look like "#/play/snake". Hash routing is deliberate: GitHub Pages
// serves static files only, so a hash route never needs a 404.html rewrite.
// Keep this file free of DOM access so it stays easy to test in isolation.

const ROUTE = /^#\/play\/([a-z0-9-]+)$/;

/** The game slug in the current URL, or null when the arcade menu is showing. */
export function currentSlug(hash = window.location.hash) {
  const match = ROUTE.exec(hash);
  return match ? match[1] : null;
}

/**
 * Replace the current history entry with a route.
 * replaceState (rather than pushState) keeps the browser Back button pointing at
 * whatever page the visitor came from, instead of trapping them inside the SPA.
 */
export function writeSlug(slug) {
  const base = window.location.href.split("#")[0];
  const next = slug ? `${base}#/play/${slug}` : base;
  if (next !== window.location.href) {
    window.history.replaceState(null, "", next);
  }
}
