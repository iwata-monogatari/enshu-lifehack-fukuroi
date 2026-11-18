(() => {
  'use strict';
  const form = document.getElementById('event-filter');
  if (!form) return;
  const month = document.getElementById('event-month');
  const place = document.getElementById('event-place');
  const access = document.getElementById('event-access');
  const past = document.getElementById('event-past');
  const cards = [...document.querySelectorAll('[data-event]')];
  const count = document.getElementById('event-count');
  const empty = document.getElementById('event-empty');
  // Only mark elapsed dates; never infer a new year's schedule or actual opening.
  const today = () => new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Tokyo', year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(new Date());
  function update() {
    const date = today();
    let visible = 0;
    cards.forEach(card => {
      const ended = !!card.dataset.end && card.dataset.end < date;
      const label = card.querySelector('[data-dated-state]');
      if (label) label.textContent = ended ? '掲載期間終了・過去の記録' : '日程発表あり・変更情報を確認';
      const matches = (!month.value || card.dataset.months.split(',').includes(month.value)) &&
        (!place.value || card.dataset.place === place.value || card.dataset.place === 'sanzan' && ['hatta', 'kasui', 'yusan'].includes(place.value)) &&
        (!access.value || card.dataset.access === access.value) && (past.checked || !ended);
      card.hidden = !matches;
      if (matches) visible++;
    });
    count.textContent = `${visible}件 / 全${cards.length}件`;
    empty.hidden = visible > 0;
  }
  form.addEventListener('change', update);
  form.addEventListener('reset', () => setTimeout(update, 0));
  function revealHash() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (target && target.matches('[data-event]') && target.hidden) {
      form.reset();
      setTimeout(() => { update(); target.scrollIntoView(); }, 0);
    }
  }
  window.addEventListener('hashchange', revealHash);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) update(); });
  form.hidden = false;
  update();
  revealHash();
})();
