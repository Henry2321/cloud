import zipfile, os, shutil, subprocess, sys

base = r'C:\Users\NGUYEN MINH TRI\OneDrive\Desktop\Cloud-_Security-_Posture-_Management\cspm-backend'
build = os.path.join(base, 'build_temp')
zip_path = os.path.join(base, 'cspm_backend_payload.zip')

if os.path.exists(build):
    shutil.rmtree(build)
os.makedirs(build)

subprocess.run([sys.executable, '-m', 'pip', 'install', '-r',
                os.path.join(base, 'requirements.txt'), '-t', build, '-q'])

for f in ['api', 'core', 'scanners', 'notifications', 'remediations']:
    shutil.copytree(os.path.join(base, f), os.path.join(build, f))

# Verify
adapter = os.path.join(build, 'core', 'database_adapter.py')
with open(adapter) as fh:
    content = fh.read()
assert 'composite key' in content, 'ERROR: composite key missing!'
print('Code verified OK')

if os.path.exists(zip_path):
    os.remove(zip_path)
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(build):
        for file in files:
            full = os.path.join(root, file)
            z.write(full, os.path.relpath(full, build))

shutil.rmtree(build)
print('ZIP OK', round(os.path.getsize(zip_path)/1024/1024, 2), 'MB')
