const area = document.querySelector('[data-guide-share]');
if (area && navigator.clipboard?.writeText) {
  const copyButton = area.querySelector('[data-share-copy]');
  const shareButton = area.querySelector('[data-share-native]');
  const status = area.querySelector('[data-share-status]');
  const canonical = document.querySelector('link[rel="canonical"]').href;
  function link(medium) {
    const url = new URL(canonical);
    url.searchParams.set('utm_source', 'fukuroi_lifehack');
    url.searchParams.set('utm_medium', medium);
    url.searchParams.set('utm_campaign', area.dataset.guideShare);
    return url.href;
  }
  copyButton.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(link('copy_link'));
      status.textContent = '共有リンクをコピーしました。';
    } catch {
      status.textContent = 'アドレス欄からページのURLをコピーできます。';
    }
  });
  area.hidden = false;
  if (typeof navigator.share === 'function') {
    shareButton.hidden = false;
    shareButton.addEventListener('click', async () => {
      try {
        await navigator.share({ title: document.querySelector('h1').textContent, url: link('share') });
      } catch (error) {
        if (error?.name !== 'AbortError') status.textContent = '共有リンクをコピーしてお使いください。';
      }
    });
  }
}
