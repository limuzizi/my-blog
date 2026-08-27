const blogList = document.querySelector('#blog-list');
const blogSubnav = document.querySelector('#blog-subnav');

function renderPosts(posts) {
  if (!posts.length) return;
  const uniquePosts = posts.filter((post, index, all) =>
    all.findIndex((item) => item.title === post.title) === index);
  if (blogList) blogList.innerHTML = uniquePosts.map((post) => `
      <a class="note-card visible" href="${post.url}">
        <time>${escapeHtml(post.date.slice(0, 7).replace('-', '.'))}</time>
        <span class="note-type">${escapeHtml(post.category)}</span>
        <h3>${escapeHtml(post.title)}</h3>
        <span class="arrow">↗</span>
      </a>`).join('');
  if (blogSubnav) blogSubnav.innerHTML = uniquePosts.map((post) => `
      <a href="${post.url}" title="${escapeHtml(post.title)}">${escapeHtml(post.title)}</a>
    `).join('');
}

if (Array.isArray(window.BLOG_POSTS) && window.BLOG_POSTS.length) {
  renderPosts(window.BLOG_POSTS);
} else if (window.location.protocol !== 'file:') {
  fetch('blogs/posts.json', { cache: 'no-store' })
    .then((response) => response.ok ? response.json() : [])
    .then(renderPosts)
    .catch(() => {});
}

function escapeHtml(value) {
  const element = document.createElement('span');
  element.textContent = value;
  return element.innerHTML;
}
