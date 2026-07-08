"""Render 3D + HTML viewer tự chứa — lớp TÁCH RỜI, engine không biết.

PNG: matplotlib trisurf trên mesh marching-cubes (không PyVista/VTK).
HTML: renderer canvas thuần JS nhúng thẳng — mở OFFLINE, không CDN.
Xoay: kéo chuột · Zoom: lăn chuột · Slider: tiến hóa qua các mốc.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import numpy as np  # noqa: E402

from geophys.export_stl import rho_to_mesh  # noqa: E402

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8">
<title>GP viewer — __TITLE__</title>
<style>
 body{margin:0;background:#111;color:#ddd;font-family:sans-serif}
 #hud{position:fixed;top:8px;left:12px;font-size:13px}
 #bar{position:fixed;bottom:12px;left:12px;right:12px;display:flex;gap:10px}
 canvas{display:block;width:100vw;height:100vh}
 input[type=range]{flex:1}
</style></head><body>
<div id="hud">GP — __TITLE__ · kéo chuột: xoay · lăn: zoom</div>
<canvas id="c"></canvas>
<div id="bar"><span id="lbl"></span><input id="frame" type="range" min="0"
 max="__MAXF__" value="__MAXF__" step="1"></div>
<script>
const FRAMES = __FRAMES__;
const LABELS = __LABELS__;
const cv = document.getElementById("c"), ctx = cv.getContext("2d");
let yaw=-0.7, pitch=0.42, zoom=1.0, fi=FRAMES.length-1, drag=null;
function center(f){const v=f.v;let c=[0,0,0];
 for(const p of v){c[0]+=p[0];c[1]+=p[1];c[2]+=p[2];}
 return c.map(x=>x/v.length);}
function draw(){
 const W=cv.width=innerWidth,H=cv.height=innerHeight;
 ctx.fillStyle="#111";ctx.fillRect(0,0,W,H);
 const f=FRAMES[fi],c=center(f);
 const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
 const s=zoom*Math.min(W,H)/ (f.scale*1.6);
 const P=f.v.map(p=>{
  let x=p[0]-c[0],y=p[1]-c[1],z=p[2]-c[2];
  let x1=x*cy+z*sy, z1=-x*sy+z*cy;
  let y2=y*cp-z1*sp, z2=y*sp+z1*cp;   // y-down của lưới: giữ nguyên hệ
  return [W/2+x1*s, H/2+y2*s, z2];});
 const light=[0.5,-0.8,0.6];
 const tris=[];
 for(const t of f.f){
  const a=P[t[0]],b=P[t[1]],d=P[t[2]];
  const z=(a[2]+b[2]+d[2])/3;
  const ux=b[0]-a[0],uy=b[1]-a[1],uz=b[2]-a[2];
  const vx=d[0]-a[0],vy=d[1]-a[1],vz=d[2]-a[2];
  let nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
  const n=Math.hypot(nx,ny,nz)||1;
  let sh=(nx*light[0]+ny*light[1]+nz*light[2])/n;
  sh=Math.abs(sh);
  tris.push([z,a,b,d,sh]);}
 tris.sort((p,q)=>p[0]-q[0]);
 for(const[t,a,b,d,sh]of tris){
  const g=Math.round(40+200*sh);
  ctx.fillStyle=`rgb(${g},${Math.round(g*0.85)},${Math.round(g*0.5)})`;
  ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);
  ctx.lineTo(d[0],d[1]);ctx.closePath();ctx.fill();}
 document.getElementById("lbl").textContent=LABELS[fi];}
cv.addEventListener("mousedown",e=>drag=[e.clientX,e.clientY]);
addEventListener("mouseup",()=>drag=null);
addEventListener("mousemove",e=>{if(!drag)return;
 yaw+=(e.clientX-drag[0])*0.01;pitch+=(e.clientY-drag[1])*0.01;
 drag=[e.clientX,e.clientY];draw();});
addEventListener("wheel",e=>{zoom*=e.deltaY<0?1.1:0.9;draw();});
document.getElementById("frame").addEventListener("input",e=>{
 fi=+e.target.value;draw();});
addEventListener("resize",draw);
draw();
</script></body></html>
"""


def _mesh_to_frame(rho: np.ndarray, iso: float, smooth_iters: int) -> dict:
    mesh, _ = rho_to_mesh(rho, iso=iso, smooth_iters=smooth_iters)
    verts = np.round(np.asarray(mesh.vertices, dtype=np.float64), 2)
    return {
        "v": verts.tolist(),
        "f": np.asarray(mesh.faces, dtype=np.int64).tolist(),
        "scale": float(max(rho.shape)),
    }


def render_isosurface(rho: np.ndarray, path, iso: float = 0.5,
                      smooth_iters: int = 5, elev: float = 22.0,
                      azim: float = -65.0) -> Path:
    """Ảnh PNG isosurface tĩnh (matplotlib trisurf, trục đúng tỷ lệ)."""
    mesh, _ = rho_to_mesh(rho, iso=iso, smooth_iters=smooth_iters)
    v, f = np.asarray(mesh.vertices), np.asarray(mesh.faces)
    fig = plt.figure(figsize=(9, 4.5), dpi=130)
    ax = fig.add_subplot(projection="3d")
    ax.plot_trisurf(v[:, 0], v[:, 2], f, v[:, 1],
                    color="#d8a24a", edgecolor="none", shade=True)
    ax.set_box_aspect((rho.shape[0], rho.shape[2], rho.shape[1]))
    ax.invert_zaxis()  # y lưới hướng xuống → vẽ cho trọng lực nhìn tự nhiên
    ax.set_axis_off()
    ax.view_init(elev=elev, azim=azim)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight", pad_inches=0.05,
                facecolor="white")
    plt.close(fig)
    return out


class SnapshotRecorder3D:
    """Callback cho optimize3d: giữ bản sao rho tại các mốc.

    Dùng: rec = SnapshotRecorder3D(every=10)
          optimize3d(spec, callback=rec)
          rec.render_pngs(dir) · rec.to_html("viewer.html")
    """

    def __init__(self, every: int = 10) -> None:
        if every < 1:
            raise ValueError(f"every phải ≥ 1, nhận {every}")
        self.every = every
        self.snapshots: list = []   # (n_iter, rho copy, compliance)

    def __call__(self, n_iter: int, rho: np.ndarray, c: float) -> None:
        if n_iter % self.every == 0:
            self.snapshots.append((n_iter, rho.copy(), float(c)))

    def add_final(self, n_iter: int, rho: np.ndarray, c: float) -> None:
        """Bổ sung khung cuối nếu vòng chót không chia hết cho every."""
        if not self.snapshots or self.snapshots[-1][0] != n_iter:
            self.snapshots.append((n_iter, rho.copy(), float(c)))

    def render_pngs(self, out_dir, iso: float = 0.5) -> list:
        paths = []
        for n_iter, rho, _ in self.snapshots:
            paths.append(render_isosurface(
                rho, Path(out_dir) / f"iso_{n_iter:04d}.png", iso=iso))
        return paths

    def to_html(self, path, iso: float = 0.5, smooth_iters: int = 5,
                title: str = "tiến hóa cấu trúc") -> Path:
        """Viewer HTML tự chứa: xoay/zoom/slider — mở offline."""
        import json as _json
        if not self.snapshots:
            raise ValueError("Chưa có snapshot nào — truyền recorder vào "
                             "optimize3d(callback=...) trước")
        frames = [_mesh_to_frame(rho, iso, smooth_iters)
                  for _, rho, _ in self.snapshots]
        labels = [f"vòng {n} · compliance {c:.3f}"
                  for n, _, c in self.snapshots]
        html = (_HTML_TEMPLATE
                .replace("__TITLE__", title)
                .replace("__MAXF__", str(len(frames) - 1))
                .replace("__FRAMES__", _json.dumps(frames))
                .replace("__LABELS__", _json.dumps(labels)))
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        return out
