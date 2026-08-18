# AI 测试工程师个人求职博客

一个无需后端、可直接部署到 GitHub Pages 的个人作品集网站。

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

## 本地预览

直接双击 `index.html` 即可；也可以在项目目录运行：

```bash
python3 -m http.server 8000
```

然后打开 `http://localhost:8000`。
