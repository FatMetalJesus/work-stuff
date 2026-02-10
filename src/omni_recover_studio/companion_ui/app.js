let selectedCase = null;

const byId = (id) => document.getElementById(id);

function tokenParam() {
  const token = byId('token').value.trim();
  return token ? `&token=${encodeURIComponent(token)}` : '';
}

async function api(path) {
  const connector = path.includes('?') ? '&' : '?';
  const response = await fetch(`${path}${connector}x=1${tokenParam()}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function loadCases() {
  const payload = await api('/api/cases');
  const list = byId('cases');
  list.innerHTML = '';
  for (const row of payload.cases) {
    const item = document.createElement('li');
    item.innerHTML = `<strong>${row.name}</strong><br><span class="mono">Updated ${row.updated_at}</span>`;
    item.onclick = () => {
      selectedCase = row.name;
      byId('filesTitle').textContent = `Files — ${row.name}`;
      loadFiles();
    };
    list.appendChild(item);
  }
}

async function loadFiles() {
  if (!selectedCase) return;
  const query = encodeURIComponent(byId('search').value.trim());
  const payload = await api(`/api/case-files?case=${encodeURIComponent(selectedCase)}&q=${query}`);
  byId('filesMeta').textContent = `${payload.count} files shown`;
  const list = byId('files');
  list.innerHTML = '';

  for (const row of payload.files) {
    const item = document.createElement('li');
    const downloadUrl = `/api/file?case=${encodeURIComponent(selectedCase)}&path=${encodeURIComponent(row.relative_path)}${tokenParam()}`;
    item.innerHTML = `${row.category} · ${row.size_bytes} bytes<br><span class="mono">${row.relative_path}</span>`;
    const openBtn = document.createElement('button');
    openBtn.textContent = 'Open';
    openBtn.onclick = () => window.open(downloadUrl, '_blank');
    item.appendChild(openBtn);
    list.appendChild(item);
  }
}

byId('reloadCases').onclick = () => loadCases().catch((err) => alert(err.message));
byId('searchBtn').onclick = () => loadFiles().catch((err) => alert(err.message));

loadCases().catch((err) => alert(err.message));
