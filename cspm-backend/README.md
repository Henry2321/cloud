# Backend

Python backend modules for CSPM scanning, notifications, remediations, and API handlers.

This folder also includes a local Node API server so the React frontend can run end-to-end on a machine without Python.

## Structure

- `api/`
- `core/`
- `notifications/`
- `remediations/`
- `scanners/`
- `tests/`

## Example commands

Go into the backend folder:

```powershell
cd backend
```

Run the local backend API:

```powershell
npm.cmd run dev
```

Build Lambda package from here:

```powershell
bash build.sh
```

Use Git Bash or WSL for `build.sh` if plain PowerShell does not have `bash`.
