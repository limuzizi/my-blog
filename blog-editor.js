const draftKey = 'yu-li-blog-draft';
const fields = {
  title: document.querySelector('#post-title'),
  category: document.querySelector('#post-category'),
  date: document.querySelector('#post-date'),
  content: document.querySelector('#post-content'),
};
const status = document.querySelector('#draft-status');

const today = new Date().toISOString().slice(0, 10);
let savedDraft = {};
try { savedDraft = JSON.parse(localStorage.getItem(draftKey) || '{}'); } catch (_) { savedDraft = {}; }

Object.entries(fields).forEach(([name, field]) => {
  field.value = savedDraft[name] || (name === 'date' ? today : '');
  field.addEventListener('input', saveDraft);
});

let statusTimer;
function saveDraft() {
  const draft = Object.fromEntries(Object.entries(fields).map(([name, field]) => [name, field.value]));
  localStorage.setItem(draftKey, JSON.stringify(draft));
  status.textContent = '草稿已保存';
  clearTimeout(statusTimer);
  statusTimer = setTimeout(() => { status.textContent = '草稿会自动保存在当前浏览器'; }, 1800);
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
  const title = fields.title.value.trim();
  const content = fields.content.value.trim();
  if (!title || !content) {
    status.textContent = '请先填写标题和正文';
    (title ? fields.content : fields.title).focus();
    return;
  }

  const button = document.querySelector('#publish-post');
  button.disabled = true;
  status.textContent = '正在保存文章…';
  try {
    const response = await fetch('/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        category: fields.category.value.trim() || '未分类',
        date: fields.date.value || today,
        content,
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || '保存失败');
    localStorage.removeItem(draftKey);
    status.innerHTML = `文章已保存 · <a href="${result.url}">查看文章 ↗</a>`;
  } catch (error) {
    status.textContent = error.message === 'Failed to fetch'
      ? '无法保存：请使用 python3 server.py 启动项目'
      : `无法保存：${error.message}`;
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
  status.textContent = '草稿已清空';
  fields.title.focus();
});
