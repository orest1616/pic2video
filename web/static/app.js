const form = document.getElementById('morph-form');
const fileInput = document.getElementById('file-input');
const statusEl = document.getElementById('status');
const resultEl = document.getElementById('result');
const videoEl = document.getElementById('video');
const downloadEl = document.getElementById('download');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const files = fileInput.files;
  if (!files || files.length < 2) {
    alert('Please select at least 2 images.');
    return;
  }
  const frames = document.getElementById('frames').value || 30;
  const fps = document.getElementById('fps').value || 30;
  const method = document.getElementById('method').value || 'classical';

  const fd = new FormData();
  for (const f of files) fd.append('files', f);
  fd.append('frames_per_transition', String(frames));
  fd.append('fps', String(fps));
  fd.append('method', method);

  statusEl.textContent = 'Processing... this may take a moment';
  resultEl.hidden = true;
  try {
    const res = await fetch('/api/v1/morph', {
      method: 'POST',
      body: fd,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `HTTP ${res.status}`);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    videoEl.src = url;
    downloadEl.href = url;
    statusEl.textContent = 'Done!';
    resultEl.hidden = false;
  } catch (err) {
    console.error(err);
    statusEl.textContent = 'Error: ' + err.message;
  }
});

