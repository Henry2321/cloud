# Frontend

React frontend for the CSPM dashboard UI.

## Run

Start the backend first, then run the frontend.

Use `npm.cmd` in PowerShell because `npm.ps1` can be blocked on this machine:

```powershell
cd ..\backend
npm.cmd run dev

cd ..\frontend
npm.cmd run dev
```

Then open `http://localhost:5173`.

The frontend proxies `/api/*` requests to `http://localhost:8000`.
