const form = document.querySelector('#filters');
const place = document.querySelector('#place');
const play = document.querySelector('#play');
const lawn = document.querySelector('#lawn');
const count = document.querySelector('#park-count');
const parks = Array.from(document.querySelectorAll('[data-park]'), item => ({
  item,
  nameAndAddress: normalize(item.querySelector('h3').textContent + item.querySelector('p').textContent)
}));

function normalize(value) {
  return value.normalize('NFKC').toLowerCase().replace(/[\s　]/g, '')
    .replace(/[ァ-ヶ]/g, ch => String.fromCharCode(ch.charCodeAt(0) - 96));
}

function display() {
  const query = normalize(place.value);
  let matches = 0;
  for (const { item, nameAndAddress } of parks) {
    const show = nameAndAddress.includes(query) &&
      (!play.checked || item.dataset.play === '1') &&
      (!lawn.checked || item.dataset.lawn === '1');
    item.hidden = !show;
    if (show) matches++;
  }
  count.textContent = matches ? matches + '件の公園' : '該当する公園がありません。町名を短くするか、条件を解除してください。';
}

form.hidden = false;
form.addEventListener('input', display);
form.addEventListener('submit', event => event.preventDefault());
form.addEventListener('reset', () => requestAnimationFrame(display));
display();
