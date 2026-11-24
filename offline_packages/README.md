# Offline Package Deployment Guide

This directory is designated for offline Python wheel packages (`.whl`) when deploying to air-gapped or restricted-network environments.

### Standard Online Execution
When connected to the internet, `run.bat` automatically installs all dependencies from `requirements.txt`:
```cmd
pip install -r requirements.txt
```

### Pre-bundling Offline Wheels (Optional for Air-Gapped Environments)
To pre-download all wheels for an offline installation, run:
```cmd
pip download -r requirements.txt -d offline_packages/
```

Then install offline using:
```cmd
pip install --no-index --find-links=offline_packages/ -r requirements.txt
```

### Required Dependencies
- `streamlit` (UI framework)
- `pandas` (Tabular data processing & CSV generation)
- `matplotlib` (Statistical and algorithmic plotting)
- `networkx` (Graph topological layout and visual rendering)
- `pytest` (Automated algorithm verification suite)
