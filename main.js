/* Renders the PROJECTS list (from projects.js) into the #project-grid. */
(function () {
  const grid = document.getElementById("project-grid");
  if (!grid || typeof PROJECTS === "undefined") return;

  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  };

  PROJECTS.forEach((p) => {
    const card = el("article", "project-card" + (p.featured ? " featured" : ""));

    const header = el("div", "project-header");
    header.appendChild(el("h3", "project-title", p.title));

    const links = el("div", "project-links");
    if (p.live) {
      const a = el("a", "project-link", "Live ↗");
      a.href = p.live;
      a.target = "_blank";
      a.rel = "noopener";
      links.appendChild(a);
    }
    if (p.source) {
      const a = el("a", "project-link", "Code ↗");
      a.href = p.source;
      a.target = "_blank";
      a.rel = "noopener";
      links.appendChild(a);
    }
    if (links.childElementCount) header.appendChild(links);
    card.appendChild(header);

    card.appendChild(el("p", "project-blurb", p.blurb));

    if (Array.isArray(p.stack) && p.stack.length) {
      const tags = el("ul", "project-stack");
      p.stack.forEach((t) => tags.appendChild(el("li", null, t)));
      card.appendChild(tags);
    }

    grid.appendChild(card);
  });
})();
