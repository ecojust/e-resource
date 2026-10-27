// Progressive enhancement: every destination remains an ordinary link without JS.
const field = document.querySelector('#landmark-search');
const cards = [...document.querySelectorAll('[data-landmark]')];
const groups = [...document.querySelectorAll('.landmark-group')];
const count = document.querySelector('#result-count');
const empty = document.querySelector('.no-results');
document.querySelector('.directory-search').hidden = false;
function filter() {
  const terms = field.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  let visible = 0;
  for (const card of cards) {
    card.hidden = !terms.every(term => card.dataset.search.toLocaleLowerCase().includes(term));
    if (!card.hidden) visible++;
  }
  for (const group of groups) group.hidden = !group.querySelector('[data-landmark]:not([hidden])');
  count.textContent = terms.length ? `找到 ${visible} / ${cards.length} 处` : `共 ${cards.length} 处`;
  empty.hidden = visible !== 0;
}
field.addEventListener('input', filter);
// Group and latest-model anchors should reveal their destination after a search.
document.querySelectorAll('a[href^="#"]').forEach(link => link.addEventListener('click', () => {
  if (field.value) { field.value = ''; filter(); }
}));
