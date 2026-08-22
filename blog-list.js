const blogList = document.querySelector('#blog-list');

fetch('blogs/posts.json', { cache: 'no-store' })
  .then((response) => response.ok ? response.json() : [])
  .then((posts) => {
    if (!posts.length) return;
    blogList.innerHTML = posts.map((post) => `
      <a class="note-card visible" href="${post.url}">
        <time>${escapeHtml(post.date.slice(0, 7).replace('-', '.'))}</time>
        <span class="note-type">${escapeHtml(post.category)}</span>
        <h3>${escapeHtml(post.title)}</h3>
        <span class="arrow">↗</span>
      </a>`).join('');
  })
  .catch(() => {});

function escapeHtml(value) {
  const element = document.createElement('span');
  element.textContent = value;
  return element.innerHTML;
}
