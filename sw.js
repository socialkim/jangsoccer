const CACHE='jangsoccer-v4';
const ASSETS=[
  './','./index.html','./css/style.css',
  './css/parts/part-01.css','./css/parts/part-02.css','./css/parts/part-03.css',
  './js/game.js',
  './js/parts/game-01.txt','./js/parts/game-02.txt','./js/parts/game-03.txt','./js/parts/game-04.txt','./js/parts/game-05.txt','./js/parts/game-06.txt',
  './manifest.webmanifest',
  './assets/images/seoul-skyline.jpg','./assets/icons/icon.svg','./assets/icons/icon-192.png','./assets/icons/icon-512.png',
  './assets/audio/stadium-crowd.wav','./assets/audio/kick.wav','./assets/audio/whistle.wav','./assets/audio/goal.wav','./assets/audio/special.wav','./assets/audio/pickup.wav'
];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  const url=new URL(event.request.url);
  if(url.origin!==location.origin)return;
  event.respondWith(caches.match(event.request).then(hit=>hit||fetch(event.request).then(response=>{const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy));return response;}).catch(()=>caches.match('./index.html'))));
});
