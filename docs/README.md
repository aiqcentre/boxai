# 📚 BoxAI Documentation

This folder contains exported HTML documentation from Jupyter notebooks for easy viewing via GitHub Pages.

---

## 📄 Available Documentation

- **[model_1.html](model_1.html)** - Week 1 Model Development & Training
- **[wrangle_visualize.html](wrangle_visualize.html)** - Data Wrangling & Visualization

---

## 🚀 Deploying to GitHub Pages

### Option 1: Deploy Entire `docs/` Folder (Recommended)

1. **Enable GitHub Pages for the repository:**
   - Go to your repository on GitHub
   - Navigate to **Settings** → **Pages**
   - Under "Source", select **Deploy from a branch**
   - Choose branch: `main` (or your default branch)
   - Choose folder: `/docs`
   - Click **Save**

2. **Access your documentation:**
   - Your docs will be available at: `https://<username>.github.io/<repository>/`
   - Example: `https://aiqcentre.github.io/boxai/`
   - Direct links:
     - Model 1: `https://aiqcentre.github.io/boxai/model_1.html`
     - Visualizations: `https://aiqcentre.github.io/boxai/wrangle_visualize.html`

3. **Wait for deployment:**
   - GitHub Pages typically takes 1-2 minutes to build and deploy
   - Check the **Actions** tab to monitor deployment progress

### Option 2: Create an Index Page

Create an `index.html` in the `docs/` folder for a landing page:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BoxAI Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 { color: #7c3aed; }
        .card {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            background: #f9fafb;
        }
        .card h2 { margin-top: 0; }
        a { color: #7c3aed; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>🎬 BoxAI Documentation</h1>
    <p>Welcome to the BoxAI project documentation. Explore our notebooks and analysis below.</p>
    
    <div class="card">
        <h2>📊 Week 1 Model Development</h2>
        <p>Comprehensive notebook covering the development and training of the Week 1 box office prediction model.</p>
        <a href="model_1.html">View Notebook →</a>
    </div>
    
    <div class="card">
        <h2>📈 Data Wrangling & Visualization</h2>
        <p>Exploratory data analysis, data cleaning, and visualization of the box office dataset.</p>
        <a href="wrangle_visualize.html">View Notebook →</a>
    </div>
    
    <hr>
    <p><small>Part of the <a href="https://github.com/aiqcentre/boxai">BoxAI Project</a></small></p>
</body>
</html>
```

### Option 3: Using GitHub Actions (Advanced)

Create `.github/workflows/deploy-docs.yml`:

```yaml
name: Deploy Documentation

on:
  push:
    branches: [ main ]
    paths:
      - 'docs/**'

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Pages
        uses: actions/configure-pages@v4
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: 'docs'
      
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

## 🔄 Updating Documentation

### Exporting Notebooks to HTML

When you update Jupyter notebooks, export them to HTML:

```bash
# From the project root
jupyter nbconvert --to html --output-dir=docs notebooks/03_week1_model_development.ipynb
jupyter nbconvert --to html --output-dir=docs notebooks/02_exploratory_analysis.ipynb
```

Or use the Jupyter interface:
1. Open notebook
2. Go to **File** → **Download as** → **HTML (.html)**
3. Save to the `docs/` folder

### Committing Changes

```bash
git add docs/
git commit -m "docs: update documentation HTML exports"
git push origin main
```

GitHub Pages will automatically rebuild and deploy your changes.

---

## 🎨 Customizing GitHub Pages

### Custom Domain

1. Add a `CNAME` file to the `docs/` folder:
   ```
   docs.boxai.example.com
   ```

2. Configure DNS records with your domain provider:
   - Type: CNAME
   - Name: docs.boxai (or your subdomain)
   - Value: `<username>.github.io`

3. In GitHub Pages settings, add your custom domain

### Themes (Optional)

Add a `_config.yml` in the `docs/` folder:

```yaml
title: BoxAI Documentation
description: Film Analytics & Box Office Prediction
theme: jekyll-theme-cayman
```

Available themes:
- `jekyll-theme-minimal`
- `jekyll-theme-cayman`
- `jekyll-theme-slate`
- `jekyll-theme-architect`

---

## 🔗 Useful Links

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Jupyter nbconvert Documentation](https://nbconvert.readthedocs.io/)
- [Jekyll Themes](https://pages.github.com/themes/)

---

## 📝 Notes

- HTML files are static and don't require server-side execution
- Notebooks are pre-rendered, so outputs are preserved
- Large files (>100MB) may cause issues - consider using Git LFS
- Update this README when adding new documentation files

---

**Last Updated:** November 2025
