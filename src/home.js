// Home page: the only job is pointing the GitHub link at the right place.
// Leave REPO_URL empty and the link removes itself instead of shipping a dead href.

const REPO_URL = "";

for (const link of document.querySelectorAll("[data-repo-link]")) {
  if (REPO_URL) {
    link.href = REPO_URL;
  } else {
    link.remove();
  }
}
