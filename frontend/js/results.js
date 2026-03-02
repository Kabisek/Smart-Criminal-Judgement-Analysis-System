// Results page – tabs and optional data from sessionStorage/API

document.addEventListener('DOMContentLoaded', function() {
  var tabButtons = document.querySelectorAll('.tab-btn');
  var tabContents = document.querySelectorAll('.tab-content');

  tabButtons.forEach(function(btn) {
    btn.addEventListener('click', function() {
      var target = btn.getAttribute('data-tab');
      tabButtons.forEach(function(b) { b.classList.remove('active'); });
      tabContents.forEach(function(c) { c.classList.remove('active'); });
      btn.classList.add('active');
      var content = document.getElementById(target + 'Tab');
      if (content) content.classList.add('active');
    });
  });

  // Placeholder / demo data when no API response is stored
  var stored = null;
  try {
    var raw = sessionStorage.getItem('analysisResult');
    if (raw) stored = JSON.parse(raw);
  } catch (e) {}

  if (stored && stored.analyzed_case) {
    renderCaseAnalysis(stored.analyzed_case);
  } else {
    setCaseAnalysisPlaceholder();
  }

  if (stored && stored.arguments_report) {
    renderArgumentsReport(stored.arguments_report);
  } else {
    setArgumentsPlaceholder();
  }

  function get(obj, path, def) {
    var p = path.split('.');
    for (var i = 0; i < p.length && obj != null; i++) obj = obj[p[i]];
    return obj != null ? obj : def;
  }

  function setCaseAnalysisPlaceholder() {
    setText('infoFileNumber', 'L-SYN-2026-XXXX');
    setText('infoDate', new Date().toLocaleDateString());
    setText('infoSubject', 'Criminal Case Analysis');
    setText('incidentTimeline', 'Case timeline will appear here after analysis.');
    setList('prosecutionLogic', ['Evidence of offence', 'Documented facts', 'Witness statements']);
    setList('defenseLogic', ['Alternative explanations', 'Procedural points', 'Reasonable doubt']);
  }

  function renderCaseAnalysis(data) {
    var header = data.case_header || {};
    setText('infoFileNumber', header.file_number || '—');
    setText('infoDate', header.date_of_analysis || '—');
    setText('infoSubject', header.subject || '—');
    var timeline = data.incident_timeline || {};
    var what = timeline.what_happened || '';
    var where = timeline.where_it_happened ? ' Where: ' + timeline.where_it_happened : '';
    setText('incidentTimeline', what + where || '—');
    var syn = data.argument_synthesis || {};
    setList('prosecutionLogic', Array.isArray(syn.prosecution_logic) ? syn.prosecution_logic : []);
    setList('defenseLogic', Array.isArray(syn.defense_logic) ? syn.defense_logic : []);
  }

  function setArgumentsPlaceholder() {
    var list = document.getElementById('similarCasesList');
    if (list) {
      list.innerHTML = '';
      ['2024_AppealCourt_September_criminal_judgment_1151', '2023_AppealCourt_March_criminal_judgment_1166'].forEach(function(id, i) {
        var div = document.createElement('div');
        div.className = 'similar-case-item';
        div.innerHTML = '<div class="case-rank">#' + (i + 1) + '</div><div class="case-details"><h4>' + id + '</h4><p>Similarity: ' + (52 - i * 2) + '%</p></div>';
        list.appendChild(div);
      });
    }
    var grid = document.getElementById('argumentsGrid');
    if (grid) {
      grid.innerHTML = '<div class="argument-card prosecution"><div class="argument-header"><h4>Precedent Support - Prosecution</h4><span class="score">0.80</span></div><p>Strong precedent support for prosecution based on similar cases.</p><div class="supporting-cases"><strong>Supporting Cases:</strong> Case-1151, Case-1166</div></div><div class="argument-card defense"><div class="argument-header"><h4>Precedent Support - Defense</h4><span class="score">0.60</span></div><p>Defense finds support in cases with procedural and evidence issues.</p><div class="model-points"><strong>Model-Extracted Points:</strong><ul><li>Evidence chain concerns</li><li>Witness credibility</li></ul></div></div>';
    }
  }

  function renderArgumentsReport(data) {
    var similar = data.similar_cases || [];
    var list = document.getElementById('similarCasesList');
    if (list) {
      list.innerHTML = '';
      similar.slice(0, 10).forEach(function(c, i) {
        var div = document.createElement('div');
        div.className = 'similar-case-item';
        var id = c.case_id || c.id || ('Case ' + (i + 1));
        var sim = (c.similarity != null ? (c.similarity * 100).toFixed(1) : (c.similarity_score != null ? (c.similarity_score * 100).toFixed(1) : '—')) + '%';
        div.innerHTML = '<div class="case-rank">#' + (i + 1) + '</div><div class="case-details"><h4>' + id + '</h4><p>Similarity: ' + sim + '</p></div>';
        list.appendChild(div);
      });
      if (similar.length === 0) list.innerHTML = '<p class="section-text">No similar cases stored.</p>';
    }

    var args = data.arguments || [];
    var grid = document.getElementById('argumentsGrid');
    if (grid && args.length) {
      grid.innerHTML = '';
      args.forEach(function(a) {
        var card = document.createElement('div');
        card.className = 'argument-card ' + (a.perspective || 'prosecution');
        var score = a.strength_score != null ? a.strength_score.toFixed(2) : '—';
        var support = Array.isArray(a.supporting_cases) ? a.supporting_cases.join(', ') : '';
        var points = Array.isArray(a.model_extracted_points) ? a.model_extracted_points.map(function(p) { return '<li>' + p + '</li>'; }).join('') : '';
        card.innerHTML = '<div class="argument-header"><h4>' + (a.title || a.perspective || 'Argument') + '</h4><span class="score">' + score + '</span></div><p>' + (a.content || '') + '</p>' + (support ? '<div class="supporting-cases"><strong>Supporting Cases:</strong> ' + support + '</div>' : '') + (points ? '<div class="model-points"><strong>Model-Extracted Points:</strong><ul>' + points + '</ul></div>' : '');
        grid.appendChild(card);
      });
    } else if (grid) {
      setArgumentsPlaceholder();
    }
  }

  function setText(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text || '—';
  }

  function setList(id, arr) {
    var el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '';
    (arr || []).forEach(function(item) {
      var li = document.createElement('li');
      li.textContent = typeof item === 'string' ? item : (item.text || JSON.stringify(item));
      el.appendChild(li);
    });
    if (el.children.length === 0) el.innerHTML = '<li>—</li>';
  }
});
