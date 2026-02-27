# Corndel Jupyter Lite

Howdy! This is the repo for https://jupyter.corndel.com/

## Setting up

Make an environemt

```bash
python -m venv .venv
```

Activate it

```bash
source .venv/bin/activate
```

Install packages

```bash
pip install -r requirements.txt
```

To build locally,

```bash
python build.py
```

To build a single module (faster iteration),

```bash
python build.py --modules python-101 --skip-base
```

To serve the built site locally,

```bash
python -m http.server -d dist 8000
```

## Deployment

Netlify is configured to rebuild and deploy on merge into `main`. See
`netlify.toml` for info.

Note that `main` is protected so don't try pushing directly - make a feature
branch and pull request.

## What is Jupyter Lite?

[Jupyter Lite](https://jupyterlite.readthedocs.io/en/stable/index.html) makes
notebooks available in the browser. It requires no installation. Jupyter Lite
kernels are designed to work with JavaScript and WASM to run cells.

## How does it handle files?

It does not have direct access to the file system. Instead, learners must import
and export data and notebooks manually. There are a few things to think about:

- If a learner creates a new notebook inside Jupyter Lite, it exists only in
  their browser's IndexDB.

- If the learner exports this notebook to save it on their machine, then they
  change the notebook in Jupyter Lite, the exported notebook is now stale
  compared to the notebook stored in IndexDB.

- If the learner wants to import data into Jupyter Lite, they click an "upload"
  button. This means that the learner is loadng the data into their browser's
  local storage. There is **no data server** - Jupyter Lite is a pure front-end
  web app and is hosted on Netlify. The word "upload" is therefore misleading.

- If a learner opens a notebook from the "handouts" folder, they are accessing a
  pre-built notebook provided by corndel. If they modify the notebook, they are
  just modifying their copy. If they refresh or close the browser, their changes
  still persist. If they delete the notebook, then the original notebook Corndel
  created will be re-downloaded from the static assets on the Netlify server.

## Data egress

The only way data can leave Jupyter Lite is if a learner writes code that
`POST`s the data somewhere. This is not a risk inherent in Jupyter Lite, or even
Python, or even programming in general. There are lots of ways a learner could
`POST` data where it shouldn't go, including WhatsApp or Royal Mail.

## Packages and kernels

You might think that adding a package to `requirements.txt` and rebuilding will
make it available in your notebooks. No. This makes the package available in the
project where Jupyter Lite is _built_, but it does not affect Jupyter's kernels
whatsoever.

Currently, for Python, we are using the Pyodide Kernel, which gives access to
packages which are
[bundled by Pyodide](https://pyodide.org/en/stable/usage/packages-in-pyodide.html).

If we need a package which is not bundled in Pyodide, we need to do something:

- Do a piplite install at the top of the notebook (easiest)

- Use a different kernel such as Xeus Python (I've looked into it - looks ok?
  Might be something for the future)

- Create and host your own Pyodide distribution (it's a world of pain, by the
  looks of it)

The piplite install looks uses Jupyter "magics":

```
%pip install -q jupysql
```

The `-q` means "quiet", and note the `%`. Using this method, you can silently
install any pure python package from pypi at the top of any notebook.

## Adding modules

Content is organised into **modules** under the `modules/` directory. Each module
gets its own isolated JupyterLite instance so learners only see relevant content.

To add a new module:

1. Create a directory under `modules/`:

   ```
   modules/
     my-new-module/
       module.json
       notebooks/
         my_notebook.ipynb
       data/
         my_data.csv
   ```

2. Add a `module.json` with a title and description:

   ```json
   {
     "title": "My New Module",
     "description": "A short description for the landing page"
   }
   ```

3. Push to main. The build script auto-discovers all module directories and
   creates a JupyterLite instance for each one. No other config changes needed.

Each module is available at `jupyter.corndel.com/{module-name}/lab/index.html`.
The landing page at `jupyter.corndel.com/` links to all modules.

### Shared content

If multiple modules need the same data files, put them in `modules/_shared/`.
Shared files are copied into every module at build time.

### How the build works

`build.py` builds JupyterLite once (the expensive part: Pyodide, extensions,
themes), then stamps out lightweight per-module copies. The heavy assets
(`build/`, `extensions/`) are shared at the root so they are not duplicated.
Adding a new module adds only a few MB to the total deployment size.
