# Configuration file for the Sphinx documentation builder.

project = 'Shepherd CLI'
copyright = '2025, Neuralis'
author = 'Neuralis'
release = '0.1.0'

# Extensions
extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_copybutton',
    'sphinx_design',
]

# Templates
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Theme - Furo (modern, clean)
html_theme = 'furo'
html_static_path = ['_static']
html_css_files = ['custom.css']

# Furo theme options
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#111111",
        "color-brand-content": "#111111",
        "color-admonition-background": "#f8f9fa",
    },
    "dark_css_variables": {
        "color-brand-primary": "#ffffff",
        "color-brand-content": "#ffffff",
    },
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "top_of_page_buttons": ["view", "edit"],
    "source_repository": "https://github.com/neuralis/shepherd-cli",
    "source_branch": "main",
    "source_directory": "docs/",
}

html_title = "Shepherd CLI"
html_favicon = "_static/favicon.svg"
html_logo = "_static/logo.svg"

# MyST settings (Markdown support)
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
]
myst_heading_anchors = 3

# Copybutton settings
copybutton_prompt_text = r">>> |\.\.\. |\$ |> "
copybutton_prompt_is_regexp = True

