const article = document.querySelector('.post-content');
const toc = document.querySelector('#post-toc-list');

if (article && toc) {
  const headings = [...article.querySelectorAll('h2, h3')];
  const usedIds = new Set();

  headings.forEach((heading, index) => {
    const base = heading.textContent
      .trim()
      .toLowerCase()
      .replace(/[^\w\u4e00-\u9fff]+/g, '-')
      .replace(/^-|-$/g, '') || `section-${index + 1}`;
    let id = base;
    let suffix = 2;
    while (usedIds.has(id) || document.getElementById(id)) id = `${base}-${suffix++}`;
    usedIds.add(id);
    heading.id = id;

    const link = document.createElement('a');
    link.href = `#${id}`;
    link.textContent = heading.textContent.trim();
    link.className = heading.tagName === 'H3' ? 'toc-subheading' : '';
    toc.append(link);
  });
}
