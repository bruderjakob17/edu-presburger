# How to Run This Project

This project contains Module that converts formulas in Presburger Arithemtic into an Automaton using the MATA library.
To install the Module, please run:

```bash
pip install -e presburger_converter 
```

It furthermore includes a Webapp with a Python FastAPI backend and a JavaScript frontend.
To locally hos the Webapp, please run:

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e presburger_converter 
pip install -r backend/requirements.txt
uvicorn backend/main:app --host 0.0.0.0 --port 8000
```

## Installation Notes (macOS only)

If you’re installing this project on macOS and encounter an error related to std::filesystem::path or a missing path in C++, it’s due to the default macOS SDK version being too old.

Before installing, set the correct deployment target to macOS 10.15 or later:

```bash
export MACOSX_DEPLOYMENT_TARGET=10.15
```
