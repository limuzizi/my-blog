const draftKey = 'yu-li-blog-draft';
const fields = {
  title: document.querySelector('#post-title'),
  category: document.querySelector('#post-category'),
  date: document.querySelector('#post-date'),
  content: document.querySelector('#post-content'),
};
const status = document.querySelector('#draft-status');
const editSlug = new URLSearchParams(window.location.search).get('edit');

function setStatus(message, state = '') {
  status.textContent = message;
  status.dataset.state = state;
}

const today = new Date().toISOString().slice(0, 10);
let savedDraft = {};
try { savedDraft = JSON.parse(localStorage.getItem(draftKey) || '{}'); } catch (_) { savedDraft = {}; }

Object.entries(fields).forEach(([name, field]) => {
  field.value = editSlug ? (name === 'date' ? today : '') : (savedDraft[name] || (name === 'date' ? today : ''));
  field.addEventListener('input', saveDraft);
});

if (editSlug && window.location.protocol !== 'file:') {
  setStatus('正在读取 Markdown 原文…', 'loading');
  fetch(`/api/posts/${encodeURIComponent(editSlug)}`, { cache: 'no-store' })
    .then(async (response) => {
      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        throw new Error('当前运行的是旧服务，请在终端停止服务后重新运行 python3 server.py');
      }
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || '读取失败');
      fields.title.value = result.title || '';
      fields.category.value = result.category || '';
      fields.date.value = result.date || today;
      fields.content.value = result.content || '';
      setStatus('正在编辑已发布文章，保存后会更新原页面', 'success');
    })
    .catch((error) => {
      const message = error instanceof TypeError
        ? '无法连接博客服务，请运行 python3 server.py'
        : error.message;
      setStatus(`无法读取文章：${message}`, 'error');
    });
}

let statusTimer;
function saveDraft() {
  const draft = Object.fromEntries(Object.entries(fields).map(([name, field]) => [name, field.value]));
  localStorage.setItem(draftKey, JSON.stringify(draft));
  setStatus('草稿已保存', 'success');
  clearTimeout(statusTimer);
  statusTimer = setTimeout(() => { setStatus('草稿会自动保存在当前浏览器'); }, 1800);
}

document.querySelector('#export-post')?.addEventListener('click', () => {
  const title = fields.title.value.trim() || '未命名文章';
  const markdown = `---\ntitle: "${title.replaceAll('"', '\\"')}"\ncategory: "${fields.category.value.trim()}"\ndate: ${fields.date.value || today}\n---\n\n# ${title}\n\n${fields.content.value}`;
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${title.replace(/[\\/:*?"<>|]/g, '-').slice(0, 60)}.md`;
  link.click();
  URL.revokeObjectURL(link.href);
});

document.querySelector('#publish-post')?.addEventListener('click', async () => {
  if (window.location.protocol === 'file:') {
    setStatus('无法发布：请先在终端运行 python3 server.py，再访问 http://localhost:4173', 'error');
    window.alert('当前页面是直接打开的本地文件，浏览器无法把文章写入项目。\n\n请在项目目录运行：python3 server.py\n然后访问：http://localhost:4173');
    return;
  }

  const title = fields.title.value.trim();
  const content = fields.content.value.trim();
  if (!title || !content) {
    setStatus('请先填写标题和正文', 'error');
    (title ? fields.content : fields.title).focus();
    return;
  }

  const button = document.querySelector('#publish-post');
  button.disabled = true;
  setStatus('正在保存文章…', 'loading');
  try {
    const response = await fetch('/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        slug: editSlug || undefined,
        title,
        category: fields.category.value.trim() || '未分类',
        date: fields.date.value || today,
        content,
      }),
    });
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error('当前服务器不支持发布，请使用 python3 server.py 启动项目');
    }
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || '保存失败');
    localStorage.removeItem(draftKey);
    status.innerHTML = `文章已保存 · <a href="${result.url}">查看文章 ↗</a>`;
    status.dataset.state = 'success';
  } catch (error) {
    const connectionError = error instanceof TypeError;
    setStatus(connectionError
      ? '无法连接发布服务：请使用 python3 server.py 启动项目'
      : `无法保存：${error.message}`, 'error');
  } finally {
    button.disabled = false;
  }
});

document.querySelector('#clear-draft')?.addEventListener('click', () => {
  if (!window.confirm('确定要清空当前草稿吗？')) return;
  fields.title.value = '';
  fields.category.value = '';
  fields.date.value = today;
  fields.content.value = '';
  localStorage.removeItem(draftKey);
  setStatus('草稿已清空', 'success');
  fields.title.focus();
});
