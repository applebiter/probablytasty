# ProbablyTasty Web Publishing

Simple PHP-based web interface for publishing your ProbablyTasty recipe collection online.

## Features

- 🔍 **Real-time Search** - Search by recipe name, ingredients, tags, or description
- 📱 **Responsive Design** - Beautiful grid layout that works on all devices
- ⚡ **Fast & Lightweight** - Pure PHP with no database required
- 🎨 **Beautiful UI** - Modern gradient design matching the app aesthetic
- 🔐 **Secure** - Includes `.htaccess` with security headers

## Installation

### 1. Export Your Recipes

In ProbablyTasty desktop app:
1. Select recipes you want to publish
2. File → Export → Select `.html` format
3. Save all recipes to export

### 2. Upload to Your Server

Upload these files to `probablytasty.applebiter.com`:

```
/public_html/
├── index.php           (main search/browse interface)
├── .htaccess           (Apache configuration)
└── recipes/            (create this directory)
    ├── recipe1.html
    ├── recipe2.html
    └── recipe3.html
```

### 3. Set Permissions

```bash
# Via SSH or cPanel Terminal
chmod 755 index.php
chmod 644 .htaccess
chmod 755 recipes
chmod 644 recipes/*.html
```

### 4. Visit Your Site

Open: https://probablytasty.applebiter.com

## Directory Structure

```
web/
├── index.php          # Main interface with search
├── .htaccess          # Apache configuration
├── recipes/           # Your exported HTML recipes
└── README.md          # This file
```

## How It Works

1. **No Database Required** - Reads recipe data directly from HTML files
2. **JSON Extraction** - Parses embedded JSON from your recipe exports
3. **Smart Search** - Searches across title, ingredients, tags, and instructions
4. **Relevance Ranking** - Scores and sorts results by match quality
5. **Click to View** - Opens full recipe HTML with interactive widgets

## Search Features

The search algorithm ranks results by:
- **Title matches** (highest priority - 10 points)
- **Description matches** (5 points)
- **Ingredient matches** (3 points)
- **Tag matches** (2 points)
- **Instruction matches** (1 point)

## Updating Your Collection

To add new recipes:

1. Export from ProbablyTasty app as HTML
2. Upload to `recipes/` directory via FTP/SFTP
3. New recipes appear automatically (no config needed)

To remove recipes:
- Delete the HTML file from `recipes/` directory

## Customization

### Change Colors

Edit `index.php` CSS section:

```css
/* Main gradient background */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Recipe card hover color */
.recipe-card:hover {
    transform: translateY(-5px);
}
```

### Change Recipes Directory

Edit line in `index.php`:

```php
$recipesDir = __DIR__ . '/recipes';  // Change 'recipes' to your directory
```

### Enable HTTPS Redirect

Uncomment in `.htaccess`:

```apache
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

## Requirements

- PHP 7.4 or higher
- Apache with `mod_rewrite` enabled
- LAMP shared hosting (you already have this ✓)

## Security Features

- Directory listing disabled
- Sensitive files blocked
- XSS protection headers
- Content type enforcement
- HTTPS redirect option

## Performance

- GZIP compression enabled
- Browser caching configured
- No database queries (file-based)
- Minimal memory usage

## Troubleshooting

### Recipes Not Showing

1. Check `recipes/` directory exists
2. Verify HTML files are valid exports
3. Check file permissions (644 for files, 755 for directory)
4. View PHP error log in cPanel

### Search Not Working

1. Ensure PHP 7.4+ is active
2. Check that recipe HTML contains embedded JSON
3. Verify `json_decode` is enabled in PHP

### 404 Errors

1. Verify `.htaccess` is uploaded and readable
2. Check Apache `mod_rewrite` is enabled
3. Confirm recipes directory path is correct

## Advanced Options

### Add Analytics

Add before `</head>` in `index.php`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=YOUR-ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'YOUR-ID');
</script>
```

### Add Sitemap Generation

Create `sitemap.php` to generate XML sitemap for SEO (optional enhancement).

## License

Same as ProbablyTasty desktop app - for personal use.

## Support

For issues with:
- **Recipe exports** - Check ProbablyTasty app
- **Web interface** - Check this README or server logs
- **Hosting setup** - Contact your hosting provider

---

Made with ❤️ for sharing delicious recipes with the world!
