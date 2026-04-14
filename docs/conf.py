project = "T3MPLATE TV Network"
copyright = "2026, AnomalyCo"
author = "AnomalyCo"
release = "1.0"

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx.ext.napoleon"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
html_static_path = ["_static"]

# Auto API docs
autosummary_generate = True
autodoc_default_options = {"members": True, "undoc-members": False}

# Asset pipeline setup
rst_epilog = """
.. toctree::
   :maxdepth: 2
   :caption: Contents:

   API <api>
   Setup <setup>
   Pipeline <pipeline>
"""
