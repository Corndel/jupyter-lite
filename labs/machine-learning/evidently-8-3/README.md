# Corndel AI6

# Module 8.3 hands-on notebook

This is a self-contained JupyterLite/Pyodide adaptation of the Module 8.3 Lesson 3 model-quality practice notebook for the AI6 Applied AI Engineering programme, adapted from the Evidently AI ML Observability Course, Module 5. The original upstream notebook is:

https://github.com/evidentlyai/ml\_observability\_course/blob/main/module5/model\_quality\_practice.ipynb

This copy keeps the original learning flow while changing the runtime mechanics so the notebook can run in a browser-based Pyodide kernel.

## Files

* `model\_quality\_practice\_corndel.ipynb`: learner notebook for JupyterLite/Pyodide.
* `README.md`: this file.
* `LICENSE`: Apache License 2.0 text retained from the upstream project.
* `requirements.txt`: optional Colab/reproduction record only. It records the pinned versions used to diagnose and fix the original Colab issue, but it is not used by the JupyterLite/Pyodide learner kernel.

## Runtime target

This notebook is designed for JupyterLite using the Pyodide Python kernel.

That means the notebook does not rely on `!pip install` or on `requirements.txt` to shape the learner kernel. In JupyterLite, NumPy, pandas and scikit-learn are provided by the Pyodide environment, so the notebook checks the available versions rather than trying to force the Colab-pinned versions into the browser runtime.

The notebook tries to install and import Evidently 0.4.19 through the JupyterLite/Pyodide package route:

```python
import piplite
await piplite.install("evidently==0.4.19")
```

If Evidently is available, the original-style Evidently `TestSuite` cells run as real Evidently checks. If Evidently cannot be installed or imported in the browser kernel, the notebook continues with transparent local teaching reports that preserve the same two learning moments.

## What this fixes

The earlier Colab triage found two separate issues in the upstream route:

1. Evidently 0.4.19 was fragile against newer NumPy and pandas versions in current Colab images.
2. The upstream `model2.pckl` file is stored with Git LFS, so a plain clone can produce a pointer file rather than a usable model artefact.

The JupyterLite version fixes those problems in a browser-safe way:

* removes Colab-style `!pip install` commands;
* does not use `requirements.txt` as a learner-kernel dependency mechanism;
* does not clone the upstream repository;
* does not load the upstream `model2.pckl` file;
* writes the feature engineering helper locally inside the notebook;
* uses a deterministic local bank-marketing-compatible dataset instead of fetching data from OpenML at runtime;
* trains the model fresh in-session;
* uses `n\_jobs=1` for browser safety;
* keeps the original `TestSuite(...)` cells visible to learners.

## Evidently behaviour

The notebook has two possible execution paths.

### Path A: Evidently is available

If `evidently==0.4.19` installs and imports successfully in the JupyterLite/Pyodide kernel, the notebook uses the real Evidently API for the two main checks:

```python
TestSuite(tests=\[NoTargetPerformanceTestPreset()])
```

and:

```python
TestSuite(tests=\[BinaryClassificationTestPreset()])
```

This is the preferred path because learners see the Evidently object pattern directly.

### Path B: Evidently is not available

If Evidently cannot run in the browser kernel, the notebook uses local compatibility classes with the same names as the Evidently classes used in the original notebook. This is deliberate. It lets the original `TestSuite(...)` cells execute without hiding the fact that learners are seeing a local teaching report rather than a full Evidently report.

The fallback report for `NoTargetPerformanceTestPreset` teaches the no-target monitoring idea by comparing reference and current batches using:

* row counts;
* positive and negative prediction rates;
* score distribution summary statistics;
* Kolmogorov-Smirnov distance for prediction-score shift;
* population stability index for score drift;
* mean confidence;
* low-confidence rate.

The fallback report for `BinaryClassificationTestPreset` teaches target-aware model quality by comparing reference and current batches using:

* target rate;
* prediction rate;
* accuracy;
* precision;
* recall;
* F1 score;
* false positive rate;
* false negative rate;
* ROC AUC;
* log loss;
* confusion matrices.

These fallback checks are not a full replacement for Evidently. They preserve the core model-quality concepts so the lesson still works when the browser kernel cannot support the full Evidently dependency chain.

## Data and model changes

The upstream notebook uses the bank marketing dataset route from the original course materials. This JupyterLite copy uses a deterministic local bank-marketing-compatible dataset generated inside the notebook. The generated data preserves the structure needed for the feature engineering helper and the model-quality exercise, while avoiding a runtime dependency on OpenML or another external data source.

The upstream route also relies on a saved model artefact. This copy trains a `RandomForestClassifier` fresh inside the notebook and saves a local `model2.pckl` file during the session. That local file is produced by the learner run. It is not an upstream dependency.

## What has not changed

The JupyterLite copy intentionally keeps the original lesson shape as far as possible:

* setup;
* helper and import preparation;
* data loading;
* feature engineering;
* train, reference and current split;
* model training;
* prediction generation;
* model output checks;
* model quality checks.

The main learner-facing headings are retained, and the two original-style `TestSuite(...)` cells remain in place.

## Data egress note

The notebook code does not post learner data to an external service. The local dataset is generated in the browser session. The only network action the notebook may attempt is package installation for `evidently==0.4.19` through the JupyterLite/Pyodide package route.

## Attribution

Adapted from the Evidently AI ML Observability Course, Module 5:

https://github.com/evidentlyai/ml\_observability\_course/blob/main/module5/model\_quality\_practice.ipynb

The upstream repository is published by Evidently AI and is licensed under the Apache License 2.0.

## Licence information

This adapted copy retains the Apache License 2.0 from the upstream project. The full licence text is included in the `LICENSE` file and should be distributed with this notebook.

The Apache License 2.0 permits use, reproduction, modification and distribution, subject to the licence conditions. In particular, redistributions should include a copy of the licence, retain relevant attribution notices, and mark modified files where appropriate.

Licence: Apache License, Version 2.0, January 2004  
Licence URL: http://www.apache.org/licenses/

