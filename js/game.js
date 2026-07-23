'use strict';
(() => {
  const parts = ['parts/game-01.txt', 'parts/game-02.txt', 'parts/game-03.txt', 'parts/game-04.txt', 'parts/game-05.txt', 'parts/game-06.txt'];
  Promise.all(parts.map((path) => fetch(new URL(path, document.currentScript.src)).then((response) => {
    if (!response.ok) throw new Error(`Failed to load ${path}: ${response.status}`);
    return response.text();
  }))).then((sources) => {
    const script = document.createElement('script');
    script.textContent = sources.join('');
    document.body.appendChild(script);
  }).catch((error) => {
    console.error(error);
    const errorScreen = document.getElementById('error');
    const menu = document.getElementById('menu');
    if (menu) menu.style.display = 'none';
    if (errorScreen) {
      errorScreen.style.display = 'grid';
      const paragraph = errorScreen.querySelector('p');
      if (paragraph) paragraph.textContent = '게임 파일을 불러오지 못했습니다. 네트워크 연결을 확인하고 새로고침해 주세요.';
    }
  });
})();
