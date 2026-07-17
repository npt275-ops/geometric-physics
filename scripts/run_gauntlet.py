# -*- coding: utf-8 -*-
"""GP GAUNTLET tren may NGUOI — chay lai 10 bai tu spec da commit.

Ky vong dang ky truoc: specs/stage3-t6-gauntlet.md (commit dddfa66).
Moi bai chay vao out_laptop/ (khong dung den bang chung sandbox trong
out/). Cham dung tieu chi da dang ky. Bai 08 DU BAO SAN se FAIL trung
thuc (OC dao dong khi preserve ~89% ngan sach) — cham la DUNG-DU-BAO.

Cach dung:  python scripts/run_gauntlet.py [--chi-bai N]
Exit 0 = 9 DAT + bai08 dung du bao. Khac = xem bang.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / "bench" / "gauntlet"
PY = sys.executable
OUT = "out_laptop"


def cli(*args):
    return subprocess.run([PY, "-m", "geophys", *args],
                          capture_output=True, text=True, cwd=ROOT)


def rho(bai):
    with np.load(G / bai / OUT / "checkpoint.npz") as d:
        return d["rho"].copy()


def rep(bai, out=OUT):
    return json.loads((G / bai / out / "report.json")
                      .read_text(encoding="utf-8"))


def chung(bai, spec_ten="spec.json"):
    r = rep(bai)
    vf = json.loads((G / bai / spec_ten).read_text(encoding="utf-8"))["volfrac"]
    return (r["status"] == "PASS" and r["converged"]
            and abs(r["volume_fraction"] - vf) <= 0.01 * vf
            and r["stl"]["watertight"] and r["stl"]["n_components"] == 1)


def chay(bai, spec_ten="spec.json", them=()):
    r = cli("run", str(G / bai / spec_ten),
            "--outdir", str(G / bai / OUT), *them)
    return r.returncode


def main():
    chi_bai = None
    if "--chi-bai" in sys.argv:
        chi_bai = int(sys.argv[sys.argv.index("--chi-bai") + 1])
    kq = {}

    def do(n, ham):
        if chi_bai is None or chi_bai == n:
            kq[f"bai{n:02d}"] = ham()

    def b01():
        if chay("bai01"):
            return {"dat": False, "loi": "run fail"}
        r = rho("bai01"); a, b = r[:, :, :3].mean(), r[:, :, 3:].mean()
        return {"dat": bool(chung("bai01") and (a - b) / b > 0.02),
                "lech_z_pct": round(float((a - b) / b * 100), 1)}

    def b02():
        if chay("bai02"):
            return {"dat": False, "loi": "run fail"}
        r = rho("bai02"); a, b = r[:16].mean(), r[16:].mean()
        return {"dat": bool(chung("bai02") and (a - b) / b > 0.05),
                "lech_x_pct": round(float((a - b) / b * 100), 1)}

    def b03():
        if chay("bai03"):
            return {"dat": False, "loi": "run fail"}
        r = rho("bai03")
        giua, toan = r[2:6, :, 2:6].mean(), r.mean()
        return {"dat": bool(chung("bai03") and giua >= toan),
                "rho_giua": round(float(giua), 3),
                "rho_toan": round(float(toan), 3)}

    def b04():
        if chay("bai04"):
            return {"dat": False, "loi": "run fail"}
        return {"dat": chung("bai04")}

    def b05():
        if chay("bai05"):
            return {"dat": False, "loi": "run fail"}
        r = rho("bai05")
        void_max = float(r[8:16, 8:16, :].max())
        vanh = np.concatenate([r[2:7, 9:11, :].ravel(),
                               r[2:7, 14:16, :].ravel(),
                               r[2:3, 11:14, :].ravel(),
                               r[6:7, 11:14, :].ravel()])
        return {"dat": bool(chung("bai05") and void_max == 0.0
                            and float(vanh.min()) == 1.0),
                "void_max": void_max, "vanh_min": float(vanh.min())}

    def b06():
        if chay("bai06") or cli(
                "run", str(G / "bai06" / "spec_single.json"),
                "--outdir", str(G / "bai06" / (OUT + "_single"))).returncode:
            return {"dat": False, "loi": "run fail"}
        from geophys.fea3d import FEA3D
        from geophys.grid3d import Grid3D
        from geophys.spec3d import load_spec3d
        spec = load_spec3d(G / "bai06" / "spec.json")
        fea = FEA3D(spec, Grid3D(spec))
        f3 = fea.forces[2]

        def c3(r):
            return fea.compliance(fea.solve(r, 3.0, force=f3), force=f3)

        with np.load(G / "bai06" / (OUT + "_single") / "checkpoint.npz") as d:
            r_s = d["rho"].copy()
        ty_so = float(c3(r_s) / c3(rho("bai06")))
        return {"dat": bool(chung("bai06") and ty_so > 1.0),
                "ty_so_c3": round(ty_so, 3)}

    def b07():
        if chay("bai07"):
            return {"dat": False, "loi": "run fail"}
        r = rep("bai07")
        return {"dat": bool(chung("bai07")
                            and abs(r["volume_fraction"] - 0.2) <= 0.002),
                "volume": r["volume_fraction"]}

    def b08():
        code = chay("bai08")
        r = rep("bai08")
        v = cli("validate", str(G / "bai08" / "spec_vuot.json"))
        chan = json.loads(v.stdout)["loi"][0]["ma"] == "GP-E-PHYSICS"
        dung_du_bao = (code == 1 and r["status"] == "FAIL"
                       and r["n_iter"] == 200 and chan)
        return {"dat": dung_du_bao, "du_bao": "FAIL-trung-thuc",
                "status": r["status"], "validator_chan_vuot": chan}

    def b09():
        c1 = chay("bai09", them=("--max-iter", "5"))
        r1 = rep("bai09")
        c2 = chay("bai09", them=("--resume-from",
                                 str(G / "bai09" / OUT / "checkpoint.npz")))
        r2 = rep("bai09")
        return {"dat": bool(c1 == 1 and r1["status"] == "FAIL"
                            and c2 == 0 and r2["status"] == "PASS"
                            and r2["n_iter"] > 5),
                "exit_lan1": c1, "exit_resume": c2, "n_iter_cuoi": r2["n_iter"]}

    def b10():
        so_vong = 0
        spec_path = G / "bai10" / "spec_v1.json"
        for v in range(1, 5):
            so_vong = v
            r = cli("validate", str(spec_path))
            kq_v = json.loads(r.stdout)
            if kq_v["trang_thai"] == "HOP_LE":
                break
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            for loi in kq_v["loi"]:
                if loi["vi_tri"].startswith("supports"):
                    spec["supports"] = [{"face": "x0", "dof": "all"}]
                elif loi["vi_tri"].startswith("preserve"):
                    spec["preserve"] = [{"type": "box", "x0": 8, "y0": 0,
                                         "z0": 0, "x1": 11, "y1": 5, "z1": 3}]
            spec_path = G / "bai10" / f"spec_laptop_v{v + 1}.json"
            spec_path.write_text(json.dumps(spec, ensure_ascii=False,
                                            indent=1), encoding="utf-8")
        code = cli("run", str(spec_path),
                   "--outdir", str(G / "bai10" / OUT)).returncode
        return {"dat": bool(so_vong <= 3 and code == 0
                            and rep("bai10")["status"] == "PASS"),
                "so_vong_sua": so_vong}

    for n, ham in enumerate((b01, b02, b03, b04, b05,
                             b06, b07, b08, b09, b10), 1):
        do(n, ham)
        if f"bai{n:02d}" in kq:
            d = kq[f"bai{n:02d}"]
            print("bai%02d %s %s" % (n, "DAT " if d["dat"] else "LECH",
                  {k: v for k, v in d.items() if k != "dat"}), flush=True)

    tong = sum(1 for d in kq.values() if d["dat"])
    print("=" * 50)
    print("GAUNTLET LAPTOP: %d/%d DAT (bai08 = DUNG-DU-BAO FAIL trung thuc)"
          % (tong, len(kq)))
    (G / "ket_qua_laptop.json").write_text(
        json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    print("luu bench/gauntlet/ket_qua_laptop.json")
    return 0 if tong == len(kq) else 1


if __name__ == "__main__":
    sys.exit(main())
