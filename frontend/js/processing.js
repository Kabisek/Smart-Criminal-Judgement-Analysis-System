// Processing page – simulate stages or call real API

document.addEventListener('DOMContentLoaded', function() {
  var progressFill = document.getElementById('progressFill');
  var progressPercent = document.getElementById('progressPercent');
  var currentStageText = document.getElementById('currentStage');
  var statusIcon = document.getElementById('statusIcon');
  var statusTitle = document.getElementById('statusTitle');
  var statusDescription = document.getElementById('statusDescription');

  var stages = [
    { id: 'stage1', name: 'File Upload', icon: '📄', duration: 800 },
    { id: 'stage2', name: 'Similarity Search', icon: '🔍', duration: 2500 },
    { id: 'stage3', name: 'Case Analysis (RAG)', icon: '🧠', duration: 4000 },
    { id: 'stage4', name: 'Arguments Report', icon: '⚔️', duration: 1500 }
  ];

  var currentStage = 0;
  var progress = 0;

  function runNext() {
    if (currentStage >= stages.length) {
      setTimeout(function() {
        window.location.href = 'results.html';
      }, 800);
      return;
    }

    var stage = stages[currentStage];
    var el = document.getElementById(stage.id);
    if (el) {
      el.querySelector('.stage-status').textContent = '⏳';
      el.querySelector('.stage-content p').textContent = 'Processing...';
    }
    if (statusIcon) statusIcon.textContent = stage.icon;
    if (statusTitle) statusTitle.textContent = stage.name;
    if (statusDescription) statusDescription.textContent = 'Processing...';
    if (currentStageText) currentStageText.textContent = stage.name;

    var targetProgress = ((currentStage + 1) / stages.length) * 100;
    var iv = setInterval(function() {
      progress += 1.5;
      if (progress >= targetProgress) {
        progress = targetProgress;
        clearInterval(iv);
      }
      if (progressFill) progressFill.style.width = progress + '%';
      if (progressPercent) progressPercent.textContent = Math.round(progress) + '%';
    }, 30);

    setTimeout(function() {
      if (el) {
        el.querySelector('.stage-status').textContent = '✓';
        el.querySelector('.stage-content p').textContent = 'Completed';
      }
      if (statusDescription) statusDescription.textContent = 'Completed';
      currentStage++;
      setTimeout(runNext, 400);
    }, stage.duration);
  }

  setTimeout(runNext, 400);
});
