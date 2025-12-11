<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ProbablyTasty Recipe Collection</title>
    <style>
        :root {
            --primary-color: #0d7377;
            --primary-dark: #0a5c5f;
            --primary-light: #14a2a8;
            --text-color: #2c3e50;
            --text-light: #7f8c8d;
            --bg-color: #ffffff;
            --card-bg: #f8f9fa;
            --border-color: #e0e0e0;
            --shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            --radius: 8px;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
            color: var(--text-color);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 50px 30px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            text-align: center;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .tagline {
            font-size: 1.2em;
            opacity: 0.95;
            font-style: italic;
        }

        .search-box {
            background: var(--bg-color);
            border-radius: var(--radius);
            padding: 30px;
            box-shadow: var(--shadow);
            margin-bottom: 30px;
        }

        .search-input {
            width: 100%;
            padding: 15px 20px;
            font-size: 18px;
            border: 2px solid var(--border-color);
            border-radius: var(--radius);
            transition: border-color 0.3s;
            font-family: inherit;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--primary-color);
        }

        .search-help {
            margin-top: 10px;
            font-size: 14px;
            color: var(--text-light);
        }

        .recipes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .recipe-card {
            background: var(--bg-color);
            border-radius: var(--radius);
            padding: 25px;
            box-shadow: var(--shadow);
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
            border: 1px solid var(--border-color);
        }

        .recipe-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 16px rgba(13, 115, 119, 0.2);
            border-color: var(--primary-light);
        }

        .recipe-title {
            font-size: 1.5em;
            margin-bottom: 10px;
            color: var(--text-color);
            font-weight: 600;
        }

        .recipe-meta {
            color: var(--text-light);
            font-size: 0.9em;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
        }

        .recipe-meta span {
            margin-right: 15px;
            display: inline-flex;
            align-items: center;
        }

        .recipe-description {
            color: var(--text-color);
            line-height: 1.6;
            margin-bottom: 15px;
        }

        .recipe-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .tag {
            background: var(--primary-color);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            transition: background-color 0.2s;
        }

        .tag:hover {
            background: var(--primary-dark);
        }

        .no-results {
            text-align: center;
            padding: 60px 20px;
            background: var(--bg-color);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            color: var(--text-light);
        }

        .no-results h2 {
            color: var(--text-color);
            margin-bottom: 10px;
        }

        .no-results a {
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
        }

        .no-results a:hover {
            text-decoration: underline;
        }

        .stats {
            text-align: center;
            background: var(--bg-color);
            padding: 15px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            color: var(--text-color);
            font-size: 1em;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
        }

        .stats strong {
            color: var(--primary-color);
        }

        footer {
            text-align: center;
            background: var(--bg-color);
            color: var(--text-color);
            margin-top: 40px;
            padding: 30px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
        }

        footer p {
            margin: 5px 0;
            color: var(--text-light);
        }

        .highlight {
            background-color: #fffacd;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🍳 ProbablyTasty</h1>
            <p class="tagline">Your Collection of Delicious Recipes</p>
        </header>

        <div class="search-box">
            <form method="GET" action="">
                <input 
                    type="text" 
                    name="q" 
                    class="search-input" 
                    placeholder="Search recipes by name, ingredient, tag, or description..."
                    value="<?php echo htmlspecialchars($_GET['q'] ?? ''); ?>"
                    autofocus
                >
                <div class="search-help">
                    Try: "chicken", "dessert", "quick meals", "vegetarian"
                </div>
            </form>
        </div>

        <?php
        // Configuration
        $recipesDir = __DIR__ . '/recipes';
        $searchQuery = trim($_GET['q'] ?? '');

        // Load all recipe HTML files
        function loadRecipes($dir) {
            $recipes = [];
            if (!is_dir($dir)) {
                return $recipes;
            }

            $files = glob($dir . '/*.html');
            foreach ($files as $file) {
                $content = file_get_contents($file);
                
                // Extract recipe data from the embedded JSON
                if (preg_match('/<script type="application\/json" id="recipe-data">(.*?)<\/script>/s', $content, $matches)) {
                    $recipeData = json_decode($matches[1], true);
                    if ($recipeData) {
                        $recipeData['filename'] = basename($file);
                        $recipes[] = $recipeData;
                    }
                }
            }
            return $recipes;
        }

        // Search recipes
        function searchRecipes($recipes, $query) {
            if (empty($query)) {
                return $recipes;
            }

            $query = strtolower($query);
            $results = [];

            foreach ($recipes as $recipe) {
                $score = 0;
                
                // Search in title (highest weight)
                if (stripos($recipe['title'], $query) !== false) {
                    $score += 10;
                }

                // Search in description
                if (!empty($recipe['description']) && stripos($recipe['description'], $query) !== false) {
                    $score += 5;
                }

                // Search in ingredients
                foreach ($recipe['ingredient_sections'] as $section) {
                    foreach ($section['ingredients'] as $ingredient) {
                        if (stripos($ingredient['name'], $query) !== false) {
                            $score += 3;
                            break 2;
                        }
                    }
                }

                // Search in tags
                foreach ($recipe['tags'] as $tag) {
                    if (stripos($tag, $query) !== false) {
                        $score += 2;
                    }
                }

                // Search in instructions
                foreach ($recipe['instruction_sections'] as $section) {
                    foreach ($section['instructions'] as $instruction) {
                        if (stripos($instruction['text'], $query) !== false) {
                            $score += 1;
                            break 2;
                        }
                    }
                }

                if ($score > 0) {
                    $recipe['score'] = $score;
                    $results[] = $recipe;
                }
            }

            // Sort by relevance score
            usort($results, function($a, $b) {
                return $b['score'] - $a['score'];
            });

            return $results;
        }

        // Highlight search terms
        function highlightText($text, $query) {
            if (empty($query)) {
                return htmlspecialchars($text);
            }
            $text = htmlspecialchars($text);
            return preg_replace('/(' . preg_quote($query, '/') . ')/i', '<span class="highlight">$1</span>', $text);
        }

        // Load and search
        $allRecipes = loadRecipes($recipesDir);
        $displayRecipes = searchRecipes($allRecipes, $searchQuery);
        ?>

        <div class="stats">
            <?php if ($searchQuery): ?>
                Found <strong><?php echo count($displayRecipes); ?></strong> recipe(s) matching "<strong><?php echo htmlspecialchars($searchQuery); ?></strong>"
                (<?php echo count($allRecipes); ?> total)
            <?php else: ?>
                Browse <strong><?php echo count($allRecipes); ?></strong> delicious recipe(s)
            <?php endif; ?>
        </div>

        <?php if (empty($displayRecipes)): ?>
            <div class="no-results">
                <h2>No recipes found</h2>
                <p>Try a different search term or <a href="index.php">browse all recipes</a></p>
            </div>
        <?php else: ?>
            <div class="recipes-grid">
                <?php foreach ($displayRecipes as $recipe): ?>
                    <div class="recipe-card" onclick="window.location.href='recipes/<?php echo htmlspecialchars($recipe['filename']); ?>'">
                        <h2 class="recipe-title"><?php echo highlightText($recipe['title'], $searchQuery); ?></h2>
                        
                        <div class="recipe-meta">
                            <?php if (!empty($recipe['prep_time'])): ?>
                                <span>⏱️ <?php echo htmlspecialchars($recipe['prep_time']); ?></span>
                            <?php endif; ?>
                            <?php if (!empty($recipe['cook_time'])): ?>
                                <span>🔥 <?php echo htmlspecialchars($recipe['cook_time']); ?></span>
                            <?php endif; ?>
                            <?php if (!empty($recipe['servings'])): ?>
                                <span>👥 <?php echo htmlspecialchars($recipe['servings']); ?> servings</span>
                            <?php endif; ?>
                        </div>

                        <?php if (!empty($recipe['description'])): ?>
                            <div class="recipe-description">
                                <?php echo highlightText(substr($recipe['description'], 0, 150) . (strlen($recipe['description']) > 150 ? '...' : ''), $searchQuery); ?>
                            </div>
                        <?php endif; ?>

                        <?php if (!empty($recipe['tags'])): ?>
                            <div class="recipe-tags">
                                <?php foreach (array_slice($recipe['tags'], 0, 5) as $tag): ?>
                                    <span class="tag"><?php echo highlightText($tag, $searchQuery); ?></span>
                                <?php endforeach; ?>
                            </div>
                        <?php endif; ?>
                    </div>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>

        <footer>
            <p>Made with ❤️ using ProbablyTasty</p>
            <p>All recipes are self-contained HTML files with interactive features</p>
        </footer>
    </div>
</body>
</html>
