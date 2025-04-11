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

To serve locally,

```bash
jupyter lite serve
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

## Adding notebooks

Anything we put in the `content/` directory is available to the learner and will
show up in their Jupyter Lite file system. These are downloaded as static assets
when the learner opens the page.

I'm suggesting we keep everything in a `content/handouts/` directory so that the
learner knows what came from Corndel. The learners own created or uploaded
content shares the same file system so we need to make sure the learner has
sovereignty over anything not in the `handouts/` subdirectory.

I'd also suggest keeping the directory structure relatively flat - just
`notebooks/` and `data/`. This is because pathing is a bit of a pain. We can
make organisation and discoverability solutions outisde of Jupyter Lite (because
each notebook gets its own URL).

An open question is: how many data sets and notebooks can we reasonably add?
It's something to return to once we get this into practice. The docs suggest not
having any files larger than 50MB. If the deployment gets too big then the app
will start to strain. There might be a possibility of hosting data elsewhere and
loading it over the network, which we could explore if needed.
