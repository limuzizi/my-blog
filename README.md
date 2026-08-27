# AI 测试工程师个人求职博客

个人作品集与博客网站。博客以 Markdown 保存原文，并自动生成可部署的 HTML 页面。

## 博客工作流

- Markdown 原文保存在 `blogs/source/`。
- 浏览页面生成到 `blogs/pages/`。
- `blogs/posts.json` 和 `blogs/posts-data.js` 保存文章目录。
- 文章页右上角的“编辑文章”会打开编辑器并读取对应 Markdown。
- 再次点击“保存并发布”会更新同一份 Markdown 和 HTML，不会创建重复文章。

## 使用前修改

1. 在 `index.html` 中替换姓名、邮箱、GitHub 地址和个人介绍。
2. 将简历命名为 `resume.pdf`，放在项目根目录。
3. 将项目卡片和学习记录中的 `href="#"` 改成真实链接。

## 部署到 GitHub Pages

1. 在 GitHub 新建公开仓库，例如 `ai-test-career-blog`。
2. 将本项目全部文件上传到仓库根目录。
3. 打开仓库的 **Settings → Pages**。
4. 在 **Build and deployment** 中选择 **Deploy from a branch**。
5. Branch 选择 `main`，目录选择 `/ (root)`，然后保存。
6. 等待一两分钟，GitHub 会显示博客访问地址。

如果仓库名是 `你的用户名.github.io`，访问地址就是 `https://你的用户名.github.io/`。

## 本地写作与预览

在项目目录运行：

```bash
python3 server.py
```

然后打开 `http://localhost:4173`。写作和编辑功能必须使用这个服务；直接双击 HTML 只能浏览，不能保存文件。

GitHub Pages 可以展示已生成的 HTML 页面，但不能在线运行 Python 保存接口。修改文章时请在本地编辑并发布，再将生成的 Markdown、HTML 和目录文件提交到 Git。
