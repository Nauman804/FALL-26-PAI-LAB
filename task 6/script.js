(() => {
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  document.addEventListener('DOMContentLoaded', ()=>{
    const clearBtn = document.getElementById('clearBtn');
    if(clearBtn){
      clearBtn.addEventListener('click', ()=>{ document.getElementById('uploadForm').reset(); });
    }

    // 3D tilt effect for video frames
    const frames = document.querySelectorAll('.video-frame');
    frames.forEach(frame => {
      const img = frame.querySelector('img');
      if(!img) return;
      let mouseX = 0, mouseY = 0, rx = 0, ry = 0;
      const onMove = (e) => {
        const r = frame.getBoundingClientRect();
        const cx = r.left + r.width/2;
        const cy = r.top + r.height/2;
        mouseX = (e.clientX - cx) / (r.width/2);
        mouseY = (e.clientY - cy) / (r.height/2);
        ry = clamp(mouseX * 10, -12, 12);
        rx = clamp(-mouseY * 10, -12, 12);
        img.style.transform = `rotateX(${rx}deg) rotateY(${ry}deg) scale(1.02)`;
      };
      const onLeave = ()=>{ img.style.transform = 'rotateX(0deg) rotateY(0deg) scale(1)'; };
      frame.addEventListener('mousemove', onMove);
      frame.addEventListener('mouseleave', onLeave);
      frame.addEventListener('mouseenter', ()=>{ img.style.transition = 'transform 0.08s ease-out'; });
    });

    // Subtle entrance animation
    requestAnimationFrame(()=> document.querySelectorAll('.card').forEach((c,i)=>{ c.style.opacity=0; setTimeout(()=>{ c.style.transition='opacity 420ms ease, transform 420ms ease'; c.style.opacity=1; c.style.transform='translateY(0)'; }, i*80);}));
  });
})();
