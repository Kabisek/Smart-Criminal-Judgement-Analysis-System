// Main JavaScript – Home & Component 2 upload

document.addEventListener('DOMContentLoaded', function() {
  var uploadArea = document.getElementById('uploadArea');
  var fileInput = document.getElementById('fileInput');
  var fileInfo = document.getElementById('fileInfo');
  var fileName = document.getElementById('fileName');
  var fileSize = document.getElementById('fileSize');
  var startBtn = document.getElementById('startAnalysisBtn');

  if (!uploadArea || !fileInput) return;

  function handleFile(file) {
    var allowed = ['.pdf', '.txt', '.json', '.docx'];
    var ext = '.' + (file.name.split('.').pop() || '').toLowerCase();
    if (allowed.indexOf(ext) === -1) {
      alert('Please upload a PDF, TXT, JSON, or DOCX file.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB.');
      return;
    }
    if (fileName) fileName.textContent = file.name;
    if (fileSize) fileSize.textContent = formatSize(file.size);
    if (fileInfo) fileInfo.style.display = 'block';
    try {
      sessionStorage.setItem('uploadFileName', file.name);
      sessionStorage.setItem('uploadFileSize', String(file.size));
    } catch (e) {}
  }

  function formatSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    var k = 1024, i = Math.floor(Math.log(bytes) / Math.log(k));
    return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + ['Bytes', 'KB', 'MB', 'GB'][i];
  }

  uploadArea.addEventListener('click', function() { fileInput.click(); });
  uploadArea.addEventListener('dragover', function(e) {
    e.preventDefault();
    uploadArea.style.background = 'rgba(107, 68, 35, 0.1)';
  });
  uploadArea.addEventListener('dragleave', function() {
    uploadArea.style.background = '';
  });
  uploadArea.addEventListener('drop', function(e) {
    e.preventDefault();
    uploadArea.style.background = '';
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener('change', function(e) {
    if (e.target.files.length) handleFile(e.target.files[0]);
  });

  if (startBtn) {
    startBtn.addEventListener('click', function() {
      var file = fileInput && fileInput.files && fileInput.files[0];
      if (!file) {
        alert('Please select a file first.');
        return;
      }
      if (window.API_BASE) {
        startBtn.disabled = true;
        startBtn.textContent = 'Uploading...';
        var fd1 = new FormData();
        fd1.append('file', file);
        var fd2 = new FormData();
        fd2.append('file', file);
        Promise.all([
          fetch(window.API_ANALYZE, { method: 'POST', body: fd1 }).then(function(r) { return r.json(); }),
          fetch(window.API_ARGUMENTS, { method: 'POST', body: fd2 }).then(function(r) { return r.json(); })
        ]).then(function(results) {
          var analysis = results[0] || {};
          var argumentsResp = results[1] || {};
          var merged = {
            analyzed_case: analysis.analyzed_case || {},
            arguments_report: argumentsResp.arguments_report || {}
          };
          if (argumentsResp.similar_cases_count != null && !merged.arguments_report.similar_cases) {
            merged.arguments_report.similar_cases = [];
          }
          try {
            sessionStorage.setItem('analysisResult', JSON.stringify(merged));
          } catch (e) {}
          window.location.href = 'processing.html';
        }).catch(function(err) {
          startBtn.disabled = false;
          startBtn.textContent = 'Start Analysis';
          console.error(err);
          alert('Backend request failed. Redirecting with demo flow. Is the API running at ' + (window.API_BASE || '') + '?');
          try { sessionStorage.removeItem('analysisResult'); } catch (e) {}
          window.location.href = 'processing.html';
        });
      } else {
        try { sessionStorage.setItem('pendingUpload', '1'); } catch (e) {}
        window.location.href = 'processing.html';
      }
    });
  }
});
