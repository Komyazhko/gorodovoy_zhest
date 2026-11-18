async function refresh(){
 try{
  const r=await fetch('/api/status',{cache:'no-store'}),s=await r.json();
  document.getElementById('connection').textContent='Связь: OK';
  document.getElementById('gesture').textContent=s.gesture;
  document.getElementById('locked').textContent=s.target_locked?'Да':'Нет';
  document.getElementById('distance').textContent=s.distance_m==null?'Нет данных':`${Number(s.distance_m).toFixed(2)} м`;
  document.getElementById('motion').textContent=s.motion;
 }catch(e){document.getElementById('connection').textContent='Нет связи'}
}
document.getElementById('stop').onclick=async()=>{await fetch('/api/stop',{method:'POST'});refresh()};
document.getElementById('enable').onclick=async()=>{await fetch('/api/enable',{method:'POST'});refresh()};
refresh();setInterval(refresh,500);
