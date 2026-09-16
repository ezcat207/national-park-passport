/* National Park Passport — interactive engine (vanilla JS, no frameworks) */
(function () {
  'use strict';

  var PARKS = window.NPP_PARKS || [];
  var CFG = window.NPP_CONFIG || { domain: 'nationalparkpassport.com', siteName: 'National Park Passport' };
  var LS_KEY = 'npp_state_v1';

  /* ---------- state ---------- */
  function blankState() {
    return { visited: {}, firstVisit: null, lastVisit: null, streak: 0, onboarded: false, quizBest: 0 };
  }
  function load() {
    try {
      var raw = localStorage.getItem(LS_KEY);
      if (!raw) return blankState();
      var s = JSON.parse(raw);
      if (!s || typeof s !== 'object' || !s.visited) return blankState();
      return Object.assign(blankState(), s);
    } catch (e) { return blankState(); }
  }
  function save() {
    try { localStorage.setItem(LS_KEY, JSON.stringify(state)); } catch (e) {}
  }
  var state = load();

  function todayStr() {
    var d = new Date();
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }
  function yesterdayStr() {
    var d = new Date(); d.setDate(d.getDate() - 1);
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }

  /* Streak: opening the site on consecutive days keeps it alive. Light touch, per design. */
  function bumpStreak() {
    var t = todayStr();
    if (!state.firstVisit) state.firstVisit = t;
    if (state.lastVisit === t) return;
    if (state.lastVisit === yesterdayStr()) { state.streak = (state.streak || 0) + 1; }
    else { state.streak = 1; }
    state.lastVisit = t;
    save();
  }

  /* ---------- derived data ---------- */
  function visitedCount() { return Object.keys(state.visited).length; }

  function levelFor(n) {
    if (n >= 51) return { name: 'Legend', next: 63, min: 51 };
    if (n >= 31) return { name: 'Ranger', next: 51, min: 31 };
    if (n >= 16) return { name: 'Adventurer', next: 31, min: 16 };
    return { name: 'Explorer', next: 16, min: 0 };
  }

  var ACH_DEFS = [
    { id: 'first',    emoji: '👣', label: 'First Steps', desc: 'Check off your first park', test: function (n) { return n >= 1; } },
    { id: 'ten',      emoji: '🥾', label: 'Trail Ten', desc: 'Visit 10 parks', test: function (n) { return n >= 10; } },
    { id: 'twenty5',  emoji: '🏕️', label: 'Quarter Way', desc: 'Visit 25 parks', test: function (n) { return n >= 25; } },
    { id: 'fifty',    emoji: '🦅', label: 'High Fifty', desc: 'Visit 50 parks', test: function (n) { return n >= 50; } },
    { id: 'all63',    emoji: '👑', label: 'All 63', desc: 'Visit every national park', test: function (n) { return n >= 63; } },
    { id: 'streak7',  emoji: '🔥', label: 'Week Warrior', desc: '7-day visit streak', test: function (n, s) { return (s.streak || 0) >= 7; } },
    { id: 'streak30', emoji: '⚡', label: 'Month Master', desc: '30-day visit streak', test: function (n, s) { return (s.streak || 0) >= 30; } }
  ];

  function stateCompletion() {
    // returns list of {code, name, total, done} for states fully visited
    var byState = {};
    PARKS.forEach(function (p) {
      p.states.forEach(function (c) {
        (byState[c] = byState[c] || { total: 0, done: 0, parks: [] });
        byState[c].total++;
        byState[c].parks.push(p);
        if (state.visited[p.slug]) byState[c].done++;
      });
    });
    return byState;
  }

  function achievements() {
    var n = visitedCount();
    var list = ACH_DEFS.map(function (a) {
      return { id: a.id, emoji: a.emoji, label: a.label, desc: a.desc, unlocked: !!a.test(n, state) };
    });
    var byState = stateCompletion();
    Object.keys(byState).sort().forEach(function (code) {
      var s = byState[code];
      if (s.total > 0 && s.done === s.total) {
        list.push({ id: 'state-' + code, emoji: '🗺️', label: code + ' Complete', desc: 'Every park in ' + code, unlocked: true });
      }
    });
    return list;
  }

  function newUnlocks(prevCount, prevAchIds) {
    var now = achievements().filter(function (a) { return a.unlocked; }).map(function (a) { return a.id; });
    return now.filter(function (id) { return prevAchIds.indexOf(id) === -1; });
  }

  /* ---------- checklist widget ---------- */
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

  function renderChecklist(root) {
    var mode = root.getAttribute('data-mode') || 'full';
    var q = (root.querySelector('[data-role=search]') || {}).value || '';
    var stateF = (root.querySelector('[data-role=state-filter]') || {}).value || '';
    var sortF = (root.querySelector('[data-role=sort]') || {}).value || 'name';

    var list = PARKS.filter(function (p) {
      if (q && p.name.toLowerCase().indexOf(q.toLowerCase()) === -1) return false;
      if (stateF && p.states.indexOf(stateF) === -1) return false;
      return true;
    });
    list.sort(function (a, b) {
      if (sortF === 'state') {
        var sa = a.states[0] + a.name, sb = b.states[0] + b.name;
        return sa < sb ? -1 : sa > sb ? 1 : 0;
      }
      return a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
    });

    var ul = root.querySelector('[data-role=list]');
    if (!ul) return;
    ul.innerHTML = '';
    var frag = document.createDocumentFragment();
    list.forEach(function (p) {
      var li = document.createElement('li');
      li.className = 'park-item' + (state.visited[p.slug] ? ' done' : '');
      li.setAttribute('role', 'checkbox');
      li.setAttribute('aria-checked', state.visited[p.slug] ? 'true' : 'false');
      li.tabIndex = 0;
      li.innerHTML = '<span class="check">✓</span><span class="park-name">' + esc(p.name) + '</span>' +
        '<span class="park-state">' + esc(p.states.join('/')) + '</span>';
      (function (park, el) {
        function toggle() { togglePark(park.slug); }
        el.addEventListener('click', toggle);
        el.addEventListener('keydown', function (e) {
          if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); toggle(); }
        });
      })(p, li);
      frag.appendChild(li);
    });
    ul.appendChild(frag);
    var countEl = root.querySelector('[data-role=count]');
    if (countEl) countEl.textContent = 'Showing ' + list.length + ' of ' + PARKS.length + ' parks';
  }

  function initChecklistWidgets() {
    document.querySelectorAll('[data-npp=checklist]').forEach(function (root) {
      ['search', 'state-filter', 'sort'].forEach(function (role) {
        var el = root.querySelector('[data-role=' + role + ']');
        if (el) el.addEventListener('input', function () { renderChecklist(root); });
      });
      // populate state filter
      var sf = root.querySelector('[data-role=state-filter]');
      if (sf && !sf.options.length) {
        var codes = {};
        PARKS.forEach(function (p) { p.states.forEach(function (c) { codes[c] = 1; }); });
        sf.innerHTML = '<option value="">All states</option>' + Object.keys(codes).sort().map(function (c) {
          return '<option value="' + c + '">' + c + '</option>';
        }).join('');
      }
      renderChecklist(root);
    });
  }

  function togglePark(slug) {
    var prevCount = visitedCount();
    var prevAch = achievements().filter(function (a) { return a.unlocked; }).map(function (a) { return a.id; });
    if (state.visited[slug]) { delete state.visited[slug]; }
    else { state.visited[slug] = todayStr(); }
    save();
    refreshAll();
    var unlocked = newUnlocks(prevCount, prevAch);
    if (unlocked.length) toast('🏆 Achievement unlocked: ' + unlocked.length + ' new badge' + (unlocked.length > 1 ? 's' : '') + '!');
  }

  function refreshAll() {
    document.querySelectorAll('[data-npp=checklist]').forEach(renderChecklist);
    document.querySelectorAll('[data-npp=stats]').forEach(renderStats);
    document.querySelectorAll('[data-npp=park-toggle]').forEach(renderParkToggle);
  }

  /* ---------- stats panel ---------- */
  function renderStats(root) {
    var n = visitedCount(), total = PARKS.length, lvl = levelFor(n);
    var pct = Math.min(100, Math.round((n / total) * 100));
    var lvlPct = lvl.next > lvl.min ? Math.round(((n - lvl.min) / (lvl.next - lvl.min)) * 100) : 100;
    var ach = achievements();
    var unlocked = ach.filter(function (a) { return a.unlocked; });

    root.innerHTML =
      '<div class="stat-big">' + n + '<span style="font-size:1.2rem;color:var(--muted)">/' + total + '</span></div>' +
      '<div class="stat-label">national parks visited</div>' +
      '<div class="progress" role="progressbar" aria-valuenow="' + pct + '" aria-valuemin="0" aria-valuemax="100"><div style="width:' + pct + '%"></div></div>' +
      '<p><span class="level-badge">⛰️ ' + lvl.name + '</span></p>' +
      '<p class="stat-label">' + (lvl.next > n ? (lvl.next - n) + ' more to reach the next level' : 'Max level reached — legend status!') + '</p>' +
      '<div class="progress" role="progressbar" aria-valuenow="' + lvlPct + '" aria-valuemin="0" aria-valuemax="100"><div style="width:' + lvlPct + '%"></div></div>' +
      '<p class="stat-label">🔥 <strong>' + (state.streak || 0) + '-day</strong> visit streak</p>' +
      '<h3>Achievements (' + unlocked.length + '/' + ach.length + ')</h3>' +
      '<div class="ach-grid">' + ach.map(function (a) {
        return '<div class="ach' + (a.unlocked ? ' unlocked' : '') + '" title="' + esc(a.desc) + '"><span class="emoji">' + a.emoji + '</span>' + esc(a.label) + '</div>';
      }).join('') + '</div>' +
      '<div data-npp="share" style="margin-top:14px"></div>';
    initShare(root.querySelector('[data-npp=share]'));
  }

  /* ---------- single park toggle (park pages) ---------- */
  function renderParkToggle(el) {
    var slug = el.getAttribute('data-slug');
    var park = PARKS.find(function (p) { return p.slug === slug; });
    var done = !!state.visited[slug];
    el.innerHTML = '<button class="btn' + (done ? ' ghost' : '') + '" style="' + (done ? 'background:var(--moss)' : '') + '">' +
      (done ? '✓ Visited — click to undo' : '＋ Mark as visited') + '</button>' +
      '<span class="stat-label">' + (done ? 'Nice! This park counts toward your ' + visitedCount() + '/63.' : 'Add ' + esc(park ? park.name : 'this park') + ' to your passport.') + '</span>';
    var btn = el.querySelector('button');
    btn.addEventListener('click', function () { togglePark(slug); });
  }

  /* ---------- toast ---------- */
  var toastTimer = null;
  function toast(msg) {
    var t = document.getElementById('npp-toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'npp-toast';
      t.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--forest-deep);color:#fff;padding:12px 22px;border-radius:99px;font-weight:700;z-index:200;box-shadow:0 10px 30px rgba(0,0,0,.3);transition:opacity .3s';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.style.opacity = '1';
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.style.opacity = '0'; }, 3200);
  }

  /* ---------- share card ---------- */
  function initShare(root) {
    if (!root) return;
    root.innerHTML = '<button class="btn small" data-role="share-btn">🎴 Generate my share card</button><div class="share-preview" data-role="share-preview"></div>';
    root.querySelector('[data-role=share-btn]').addEventListener('click', function () {
      var canvas = drawShareCard();
      var prev = root.querySelector('[data-role=share-preview]');
      prev.innerHTML = '';
      prev.appendChild(canvas);
      var a = document.createElement('a');
      a.className = 'btn small ghost';
      a.style.marginTop = '10px';
      a.textContent = '⬇ Download PNG';
      a.download = 'my-national-park-passport.png';
      a.href = canvas.toDataURL('image/png');
      prev.appendChild(document.createElement('br'));
      prev.appendChild(a);
    });
  }

  function drawShareCard() {
    var n = visitedCount(), lvl = levelFor(n);
    var unlocked = achievements().filter(function (a) { return a.unlocked; }).length;
    var c = document.createElement('canvas');
    c.width = 1080; c.height = 1080;
    var x = c.getContext('2d');
    var g = x.createLinearGradient(0, 0, 1080, 1080);
    g.addColorStop(0, '#122619'); g.addColorStop(1, '#2e5c40');
    x.fillStyle = g; x.fillRect(0, 0, 1080, 1080);
    x.strokeStyle = 'rgba(255,255,255,.25)'; x.lineWidth = 6;
    x.strokeRect(40, 40, 1000, 1000);
    x.textAlign = 'center'; x.fillStyle = '#fff';
    x.font = '90px sans-serif'; x.fillText('🏔️', 540, 210);
    x.font = 'bold 64px sans-serif'; x.fillText('My National Park Passport', 540, 320);
    x.font = 'bold 200px sans-serif'; x.fillStyle = '#e07b39';
    x.fillText(n + '', 540, 560);
    x.font = '56px sans-serif'; x.fillStyle = '#fff';
    x.fillText('/ 63 parks visited', 540, 640);
    x.font = '48px sans-serif'; x.fillStyle = '#d9a441';
    x.fillText('⛰️ ' + lvl.name + '   •   🏆 ' + unlocked + ' achievements', 540, 740);
    x.fillText('🔥 ' + (state.streak || 0) + '-day streak', 540, 820);
    x.font = '40px sans-serif'; x.fillStyle = 'rgba(255,255,255,.75)';
    x.fillText(CFG.domain, 540, 960); // site watermark
    x.font = '32px sans-serif';
    x.fillText('Track yours free — no signup', 540, 915);
    return c;
  }

  /* ---------- onboarding (home, first visit) ---------- */
  function initOnboarding() {
    if (state.onboarded || !document.querySelector('[data-npp=onboarding]')) return;
    var steps = [
      { t: 'Welcome, explorer! 🏔️', b: 'This is your gamified checklist for all 63 U.S. national parks. Tap any park to check it off — your progress saves automatically in this browser.' },
      { t: 'Level up & earn badges 🎖️', b: 'Visiting parks moves you from Explorer to Legend. Unlock achievements for milestones, state completions, and daily visit streaks.' },
      { t: 'Share your journey 🎴', b: 'Generate a share card anytime to show off your progress. Ready? Start checking off parks below!' }
    ];
    var i = 0;
    var bd = document.createElement('div');
    bd.className = 'modal-backdrop';
    bd.innerHTML = '<div class="modal" role="dialog" aria-modal="true"><div class="steps" data-role="step-label"></div><h2 data-role="t"></h2><p data-role="b"></p><div class="modal-actions"><button class="btn ghost" data-role="skip">Skip</button><button class="btn" data-role="next">Next →</button></div></div>';
    document.body.appendChild(bd);
    function show() {
      bd.querySelector('[data-role=step-label]').textContent = 'Step ' + (i + 1) + ' of ' + steps.length;
      bd.querySelector('[data-role=t]').textContent = steps[i].t;
      bd.querySelector('[data-role=b]').textContent = steps[i].b;
      bd.querySelector('[data-role=next]').textContent = i === steps.length - 1 ? "Let's go! 🎉" : 'Next →';
    }
    function done() { state.onboarded = true; save(); bd.classList.remove('show'); }
    bd.querySelector('[data-role=next]').addEventListener('click', function () { i++; if (i >= steps.length) done(); else show(); });
    bd.querySelector('[data-role=skip]').addEventListener('click', done);
    show();
    setTimeout(function () { bd.classList.add('show'); }, 600);
  }

  /* ---------- quiz ---------- */
  function initQuiz() {
    var root = document.querySelector('[data-npp=quiz]');
    if (!root || !window.NPP_QUIZ) return;
    var qs = window.NPP_QUIZ, idx = 0, score = 0;
    function renderQ() {
      var q = qs[idx];
      root.innerHTML = '<div class="quiz-q"><p class="stat-label">Question ' + (idx + 1) + ' of ' + qs.length + ' — Score: ' + score + '</p><h3>' + esc(q.q) + '</h3>' +
        '<ul class="quiz-opts">' + q.options.map(function (o, oi) {
          return '<li><button data-i="' + oi + '">' + esc(o) + '</button></li>';
        }).join('') + '</ul><div class="quiz-explain" data-role="explain"></div>' +
        '<button class="btn small" data-role="next" style="display:none;margin-top:10px">' + (idx === qs.length - 1 ? 'See my result →' : 'Next question →') + '</button></div>';
      root.querySelectorAll('.quiz-opts button').forEach(function (b) {
        b.addEventListener('click', function () {
          var pick = parseInt(b.getAttribute('data-i'), 10);
          var ok = pick === q.answer;
          if (ok) score++;
          root.querySelectorAll('.quiz-opts button').forEach(function (bb, bi) {
            bb.disabled = true;
            if (bi === q.answer) bb.classList.add('correct');
            else if (bi === pick) bb.classList.add('wrong');
          });
          var ex = root.querySelector('[data-role=explain]');
          ex.innerHTML = (ok ? '✅ Correct! ' : '❌ Not quite. ') + esc(q.explain);
          ex.classList.add('show');
          root.querySelector('[data-role=next]').style.display = 'inline-block';
        });
      });
      root.querySelector('[data-role=next]').addEventListener('click', function () {
        idx++;
        if (idx < qs.length) renderQ(); else renderResult();
      });
    }
    function renderResult() {
      var msg = score === qs.length ? 'Perfect score! Certified park nerd. 🏆' :
        score >= 7 ? 'Excellent! You know your parks. 🌲' :
        score >= 4 ? 'Solid! A few more park trips will fix the rest. 🥾' :
        'Every expert starts somewhere — time to plan a park trip! 🗺️';
      if (score > (state.quizBest || 0)) { state.quizBest = score; save(); }
      root.innerHTML = '<div class="quiz-result show"><div class="score">' + score + '/' + qs.length + '</div><p>' + esc(msg) + '</p>' +
        '<p class="stat-label" style="color:#cfe0cb">Your best score: ' + (state.quizBest || score) + '/' + qs.length + ' (saved in this browser)</p>' +
        '<button class="btn" id="quiz-retry">Try again</button> <a class="btn ghost" href="/">Back to the checklist</a></div>';
      document.getElementById('quiz-retry').addEventListener('click', function () { idx = 0; score = 0; renderQ(); });
    }
    renderQ();
  }

  /* ---------- nav toggle ---------- */
  function initNav() {
    var btn = document.querySelector('.nav-toggle');
    var nav = document.querySelector('.main-nav');
    if (!btn || !nav) return;
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    // mark active link
    var path = location.pathname;
    nav.querySelectorAll('a').forEach(function (a) {
      var href = a.getAttribute('href');
      if (href === path || (href !== '/' && path.indexOf(href) === 0)) a.classList.add('active');
    });
  }

  /* ---------- boot ---------- */
  document.addEventListener('DOMContentLoaded', function () {
    bumpStreak();
    initNav();
    initChecklistWidgets();
    document.querySelectorAll('[data-npp=stats]').forEach(renderStats);
    document.querySelectorAll('[data-npp=park-toggle]').forEach(renderParkToggle);
    initOnboarding();
    initQuiz();
  });
})();
