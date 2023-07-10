# GitHub Pages Documentation

This project uses [Github Pages](https://pages.github.com/) to host a static site. The static site uses
HTML as opposed to markdown, so there is a broader range of possible customization. To generate the HTML in the static site,
we use [MKDocs](https://www.mkdocs.org) alongside [Material](https://squidfunk.github.io/mkdocs-material),
and [mkdocstrings-python](https://mkdocstrings.github.io/python/), which allows us to use markdown files to write our 
site and also automate our release process using [GitHub Actions](https://github.com/features/actions).


## MKDocs Project Structure

The `mkdocs.yml` file located at the project's root defines the project's main configuration, which includes plugins,
themes, and markdown extensions. All the documentation for the project's site is in the `docs` directory, the default
entry point used by MKDocs.

## Python Library Documentation

To write the documentation of our [vmware-aria-operations-integration-sdk-lib](lib/python), we use 
[mkdocstrings](https://mkdocstrings.github.io/python/), which allows us to auto-generate our code's documentation by 
reading our code structure along with the docstrings throughout the code. By default, mkdocstrings uses 
[Google-Style docstrings](https://google.github.io/styleguide/pyguide.html), so all of our docstrings follow them.

## Development

1. install all development dependencies in your local virtual environment:

```
poetry install --only=dev
```

2. Start the MKDocs development service to host a local site with hot-reload:

```
mkdocs serve
```

3. Voila! Ready to develop. Edit/create a file inside the `docs` folder and use regular markdown notation. The additional markdown can also be used as part of the Markdown extensions. References to the markdown extensions will be based on the extension, but most references come from Material's [reference page](https://squidfunk.github.io/mkdocs-material/reference/).


4. Open a PR. Once the PR is merged, the action defined at .github/workflows/documentation.yml will trigger and re-generate the new site.


