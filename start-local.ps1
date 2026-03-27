$workspace = "C:\Users\NGUYEN MINH TRI\OneDrive\Desktop\CSPM"

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd '$workspace\\backend'; npm.cmd run dev"
)

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd '$workspace\\frontend'; npm.cmd run dev"
)
