# CSPM

This repository is now split into two top-level folders:

- `backend/` for Python CSPM scanning logic and API handlers
- `frontend/` for the React dashboard UI

## Run the full system locally

Open two PowerShell terminals.

Terminal 1:

```powershell
cd backend
npm.cmd run dev
```

Terminal 2:

```powershell
cd frontend
npm.cmd run dev
```

Open `http://localhost:5173`.

## Run frontend only

Use PowerShell:

```powershell
cd frontend
npm.cmd run dev
```

Open `http://localhost:5173`.

## Build frontend

```powershell
cd frontend
npm.cmd run build
```

Production files will be created in `frontend/dist`.

## Backend location

The backend files are now under `backend/`.

Example:

```powershell
cd backend
```
