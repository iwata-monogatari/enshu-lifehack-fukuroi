(() => {
  'use strict';
  const form = document.getElementById('food-filter');
  if (!form) return;
  const query = document.getElementById('food-query');
  const kind = document.getElementById('food-kind');
  const area = document.getElementById('food-area');
  const count = document.getElementById('food-count');
  const empty = document.getElementById('food-empty');
  const normalize = value => value.normalize('NFKC').toLocaleLowerCase('ja');
  const cards = [...document.querySelectorAll('[data-food]')].map(node => ({node, text: normalize(node.textContent)}));
  function update() {
    const words = normalize(query.value).trim().split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const {node, text} of cards) {
      const match = (!kind.value || node.dataset.kind === kind.value) && (!area.value || node.dataset.area === area.value) && words.every(word => text.includes(word));
      node.hidden = !match;
      if (match) shown++;
    }
    count.textContent = `${shown}件 / 全${cards.length}件`;
    empty.hidden = shown !== 0;
  }
  form.hidden = false;
  form.addEventListener('submit', event => event.preventDefault());
  form.addEventListener('input', update);
  form.addEventListener('change', update);
  form.addEventListener('reset', () => setTimeout(update, 0));
  // An incoming link to a shop must remain reachable after filtering.
  window.addEventListener('hashchange', () => {
    const target = document.getElementById(location.hash.slice(1));
    if (target?.matches('[data-food]') && target.hidden) {
      form.reset();
      setTimeout(() => target.scrollIntoView(), 0);
    }
  });
  update();
})();
