const editorAccessKey = 'blog-editor-unlocked';
const editorTapCountKey = 'blog-editor-tap-count';
const requiredBlogTaps = 10;

function updateEditorAccess() {
  const unlocked = localStorage.getItem(editorAccessKey) === 'true';
  document.querySelectorAll('[data-editor-access]').forEach((element) => {
    element.hidden = !unlocked;
  });
}

updateEditorAccess();

document.querySelector('#blog-nav-link')?.addEventListener('click', (event) => {
  if (localStorage.getItem(editorAccessKey) === 'true') return;
  event.preventDefault();
  const taps = Number(localStorage.getItem(editorTapCountKey) || 0) + 1;
  if (taps >= requiredBlogTaps) {
    localStorage.setItem(editorAccessKey, 'true');
    localStorage.removeItem(editorTapCountKey);
    updateEditorAccess();
    return;
  }
  localStorage.setItem(editorTapCountKey, String(taps));
});
