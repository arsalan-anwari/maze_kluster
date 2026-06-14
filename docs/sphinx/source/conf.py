import sys
from pathlib import Path

sys.path.insert(0, str(Path("../../../src").resolve()))

project = "maze-kluster"
author = "Arsalan Anwari"
release = "0.1.0"
copyright = "2026, Arsalan Anwari"

extensions = [
    "sphinxawesome_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

html_theme = "sphinxawesome_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_title = "maze-kluster"

pygments_style = "default"
pygments_dark_style = "monokai"

_GITHUB_ICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">'
    '<path d="M12 2C6.475 2 2 6.475 2 12a10 10 0 006.838 9.488c.5.087.687-.213.687-.476'
    " 0-.237-.013-.868-.013-1.703-2.782.604-3.369-1.341-3.369-1.341-.454-1.156-1.11-1.463-1.11-1.463"
    "-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832"
    ".092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683"
    "-.103-.253-.446-1.27.098-2.647 0 0 .84-.268 2.75 1.026A9.578 9.578 0 0112 6.836c.85.004"
    " 1.705.114 2.504.337 1.909-1.294 2.748-1.026 2.748-1.026.546 1.377.202 2.394.1 2.647"
    ".64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852"
    " 0 1.336-.012 2.415-.012 2.742 0 .268.18.578.688.48A10.02 10.02 0 0022 12c0-5.525-4.475-10-10-10z\"/>"
    "</svg>"
)

# Package cube icon — represents a published Python package
_PYPI_ICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">'
    '<path d="M21 16.5c0 .38-.21.71-.53.88l-7.9 4.44c-.16.12-.36.18-.57.18-.21 0-.41-.06-.57-.18'
    "l-7.9-4.44A1 1 0 013 16.5v-9c0-.38.21-.71.53-.88l7.9-4.44c.16-.12.36-.18.57-.18"
    ".21 0 .41.06.57.18l7.9 4.44c.32.17.53.5.53.88v9z"
    "M12 4.15L6.04 7.5 12 10.85l5.96-3.35L12 4.15z"
    'M5 15.91l6 3.38v-6.71L5 9.21v6.7zm8 3.38l6-3.38V9.21l-6 3.38v6.7z"/>'
    "</svg>"
)

html_theme_options = {
    "show_prev_next": True,
    "show_scrolltop": True,
    "extra_header_link_icons": {
        "GitHub": {
            "link": "https://github.com/arsalan-anwari/maze_kluster",
            "icon": _GITHUB_ICON,
        },
        "PyPI": {
            "link": "#",  # fill in after publishing
            "icon": _PYPI_ICON,
        },
    },
}

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "special-members": "__init__",
}

autodoc_mock_imports = [
    "networkx",
    "pandas",
    "sklearn",
    "pydantic",
    "pyarrow",
    "requests",
    "textual",
    "hightech_amazeing",
]
