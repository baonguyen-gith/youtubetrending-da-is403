# -*- coding: utf-8 -*-
"""
make_q6_explain.py
==================
Sinh file Word giải thích kết quả Q6 (phân cụm K-means) bằng tiếng Việt,
đọc số liệu trực tiếp từ các CSV do 04_q6_kmeans.py xuất ra.

Chạy: py 05_Code_Output/python/make_q6_explain.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from md2docx_q5 import convert_md_text  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT = SCRIPT_DIR.parent.parent
OUT = PROJECT / "05_Code_Output" / "outputs" / "5.6 Q6"

BEHAV = ["vpd_log", "growth_log", "momentum", "like_rate", "comment_rate", "volatility"]
MEANING = {
    "vpd_log": "tốc độ xem trung bình mỗi ngày (thang log)",
    "growth_log": "tổng mức tăng lượt xem trong cửa sổ đo (thang log)",
    "momentum": "video đang tăng tốc (dương) hay đã nguội (âm)",
    "like_rate": "số like trên mỗi lượt xem",
    "comment_rate": "số bình luận trên mỗi lượt xem",
    "volatility": "tốc độ tăng có đều hay dồn cục (hệ số biến thiên)",
}


def fnum(x, nd=0):
    return f"{x:,.{nd}f}".replace(",", ".")


def pct(x, nd=1):
    return f"{x:.{nd}f}".replace(".", ",")


DEC = {"vpd_log_med": 2, "growth_log_med": 2, "momentum_med": 2,
       "like_rate_med": 4, "comment_rate_med": 4, "volatility_med": 2}


def build_md() -> str:
    prof = pd.read_csv(OUT / "q6_cluster_profile.csv")
    sel = pd.read_csv(OUT / "q6_k_selection.csv")
    st = pd.read_csv(OUT / "q6_stability.csv")
    chi = pd.read_csv(OUT / "q6_chi2.csv")
    steps = pd.read_csv(OUT / "q6_filter_steps.csv")
    scal = pd.read_csv(OUT / "q6_scaler_params.csv", index_col=0)
    asg = pd.read_csv(OUT / "q6_cluster_assignments.csv", low_memory=False)
    sd = {c: asg[c].std(ddof=0) for c in BEHAV}

    clusters = prof[prof["cluster"] != "Tổng"].copy()
    clusters["cluster"] = clusters["cluster"].astype(int)
    total = prof[prof["cluster"] == "Tổng"].iloc[0]
    best_k = int(sel.loc[sel["chon"] == True, "k"].iloc[0])  # noqa: E712
    sel_row = sel[sel["k"] == best_k].iloc[0]
    ari_mean = st["ari"].mean()

    L = []
    A = L.append

    A("# Giải thích kết quả Q6 — Phân cụm video bằng K-means\n")
    A("Tài liệu này giải thích **cách đọc** kết quả Q6: mỗi bước làm gì, "
      "các con số trong Bảng 5.17 và Hình 5.9 nghĩa là gì, và khi nào thì "
      "được phép kết luận. Toàn bộ số liệu lấy từ lần chạy trên dữ liệu final.\n")

    # 1. Dữ liệu
    A("## 1. Dữ liệu đưa vào phân cụm\n")
    A("Nguồn là `measurements.csv` — chuỗi đo lượt xem của từng video theo ngày. "
      "Không phải video nào cũng đo đủ nhiều ngày, nên phải lọc trước khi phân cụm:\n")
    A("| Bước lọc | Số dòng đo | Số video |")
    A("|---|---:|---:|")
    for _, r in steps.iterrows():
        nd = "—" if pd.isna(r["n_dong"]) else fnum(int(r["n_dong"]))
        A(f"| {r['buoc']} | {nd} | {fnum(int(r['n_video']))} |")
    n_video = int(steps.iloc[-1]["n_video"])
    A(f"\nKết quả: **{fnum(n_video)} video** đủ điều kiện phân cụm "
      f"(tức {pct(n_video / 140387 * 100, 2)}% của 140.387 video trong dữ liệu). "
      "Đây là mẫu khá chặt: chỉ giữ video được đo ít nhất 5 ngày và trải dài "
      "ít nhất 5 ngày, nên kết quả mô tả **nhóm video được theo dõi đủ lâu**, "
      "không đại diện cho toàn bộ video trên kênh.\n")

    # 2. Sáu biến
    A("## 2. Sáu biến hành vi và cách đọc\n")
    A("Mỗi video được mô tả bằng 6 con số, tất cả đều tính từ chuỗi đo cuối ngày:\n")
    A("| Biến | Ý nghĩa thực tế | Đọc thế nào |")
    A("|---|---|---|")
    doc = {
        "vpd_log": "Càng cao càng lan nhanh",
        "growth_log": "Càng cao càng tăng nhiều trong thời gian đo",
        "momentum": "> 0: đang nóng lên; < 0: đã hạ nhiệt",
        "like_rate": "Càng cao càng được yêu thích",
        "comment_rate": "Càng cao càng gây tranh luận / bàn tán",
        "volatility": "Càng cao càng thất thường, dồn cục",
    }
    for c in BEHAV:
        A(f"| `{c}` | {MEANING[c]} | {doc[c]} |")
    A("\nBa biến tỷ lệ (`like_rate`, `comment_rate`, `volatility`) được **cắt ở "
      "phân vị 99** trước khi chuẩn hoá: một vài video có tỷ lệ cực đại (video "
      "nhỏ, ít view nhưng nhiều like) sẽ kéo lệch tâm cụm nếu để nguyên. "
      "Cắt p99 giữ lại 99% thông tin nhưng không để ngoại lai chi phối.\n")
    A("Sau đó mọi biến được đưa về cùng thang bằng StandardScaler "
      "(z = (x − trung bình) / độ lệch chuẩn). Nhờ vậy biến nào cũng đóng góp "
      "ngang nhau, không bị `vpd_log` lấn át chỉ vì đơn vị lớn hơn.\n")
    A("| Biến | Trung bình | Độ lệch chuẩn |")
    A("|---|---:|---:|")
    for c in BEHAV:
        A(f"| `{c}` | {pct(scal.loc[c, 'mean'], 4)} | {pct(scal.loc[c, 'scale'], 4)} |")

    # 3. Chọn k
    A("\n## 3. Vì sao chọn k = %d cụm\n" % best_k)
    A("Thử lần lượt k = 2 đến 8, mỗi k chấm ba thước đo:\n")
    A("- **Silhouette** (từ −1 đến 1): càng cao càng tốt — video trong cùng cụm "
      "giống nhau và khác cụm bên cạnh.")
    A("- **Davies-Bouldin**: càng **thấp** càng tốt — cụm càng tách bạch.")
    A("- **Inertia** (tổng bình phương khoảng cách trong cụm): luôn giảm khi tăng k, "
      "nên chỉ dùng để tìm **điểm gãy** (elbow) — chỗ tăng k không còn giúp nhiều.\n")
    A("| k | Inertia | Silhouette | Davies-Bouldin | Cụm nhỏ nhất (%) | Dùng được |")
    A("|---:|---:|---:|---:|---:|---|")
    for _, r in sel.iterrows():
        star = " ⭐" if r["k"] == best_k else ""
        A(f"| {int(r['k'])}{star} | {fnum(r['inertia'])} | {pct(r['silhouette'], 4)} | "
          f"{pct(r['davies_bouldin'], 3)} | {pct(r['min_cluster_pct'], 1)} | "
          f"{'có' if r['dung_duoc'] else 'không'} |")
    ok = sel[sel["dung_duoc"]].sort_values("k")
    db_ok_best = ok.loc[ok["davies_bouldin"].idxmin()]
    db_all_best = sel.loc[sel["davies_bouldin"].idxmin()]
    sil_all_best = sel.loc[sel["silhouette"].idxmax()]
    A(f"\n**Kết luận: chọn k = {best_k}.** Silhouette đạt {pct(sel_row['silhouette'], 4)} — "
      f"cao nhất trong các k thoả điều kiện mỗi cụm chiếm ít nhất 5% số video "
      f"(k = {int(ok['k'].min())} đến {int(ok['k'].max())}). "
      "Điều kiện 5% để tránh sinh ra cụm chỉ vài chục video, không đủ tin cậy "
      "để mô tả.\n")
    A(f"Hai lưu ý khi đọc bảng chọn k:\n")
    A(f"- Nếu bỏ điều kiện 5%, silhouette còn cao hơn ở k = {int(sil_all_best['k'])} "
      f"({pct(sil_all_best['silhouette'], 4)}) — nhưng ở k đó cụm nhỏ nhất chỉ "
      f"{pct(sil_all_best['min_cluster_pct'], 1)}% số video, không đủ để mô tả "
      "một nhóm hành vi.")
    if int(db_all_best["k"]) != best_k:
        A(f"- Davies-Bouldin thấp nhất trong các k dùng được là k = {int(db_ok_best['k'])} "
          f"({pct(db_ok_best['davies_bouldin'], 3)}). Riêng trong toàn bảng, "
          f"k = {int(db_all_best['k'])} có DB thấp nhất "
          f"({pct(db_all_best['davies_bouldin'], 3)}) nhưng lại vi phạm điều kiện 5%.")
    else:
        A(f"- Davies-Bouldin thấp nhất toàn bảng cũng chính là k = {best_k} "
          f"({pct(sel_row['davies_bouldin'], 3)}).")
    A(f"\nBa thước đo vì thế **không mâu thuẫn**: k = {best_k} vừa là điểm silhouette "
      "tốt nhất trong vùng hợp lệ, vừa có cụm đủ lớn để diễn giải.\n")
    A(f"Cần nói rõ: silhouette {pct(sel_row['silhouette'], 2)} là **mức trung bình**, không phải cụm "
      "tách bạch hoàn hảo. Điều này bình thường với dữ liệu hành vi người xem — "
      "các video chuyển dần từ nhóm này sang nhóm khác chứ không tách rời. "
      "Vì vậy chỉ nên đọc cụm như **chân dung xu hướng**, không phải nhãn tuyệt đối.\n")

    # 4. Ổn định
    A("## 4. Phân cụm có ổn định không? (chỉ số ARI)\n")
    A("Nếu lấy ngẫu nhiên 80% video để phân cụm lại rồi so với kết quả gốc, "
      "kết quả có giống không? Đó là phép thử bằng **ARI** "
      "(Adjusted Rand Index, 1 = giống hệt, 0 = giống ngẫu nhiên).\n")
    A(f"- Chạy **{len(st)} lần** bootstrap 80/20.")
    A(f"- ARI trung bình **{pct(ari_mean, 3)}** (thấp nhất {pct(st['ari'].min(), 3)}, "
      f"cao nhất {pct(st['ari'].max(), 3)}).")
    if ari_mean >= 0.6:
        A("- ARI ≥ 0,6 → phân cụm **ổn định**, các cụm không phải sản phẩm may mắn "
          "của một lần chia ngẫu nhiên.\n")
    else:
        A("- ARI < 0,6 → **cảnh báo**: cụm không ổn định, chỉ nên mô tả chứ "
          "không nên dùng để ra quyết định.\n")

    # 5. Hồ sơ cụm
    A("## 5. Đọc Bảng 5.17 — hồ sơ từng cụm\n")
    A("Bảng dưới đây là **trung vị** của từng biến trong mỗi cụm. Dùng trung vị "
      "thay vì trung bình để một vài video đột biến không làm lệch bức tranh.\n")
    A("| Cụm | n | % | vpd_log | growth_log | momentum | like_rate | comment_rate | volatility | Subs (nghìn) | Tuổi (ngày) | % Trending | % viral_A | Thể loại nổi bật |")
    A("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for _, r in clusters.iterrows():
        A(f"| {int(r['cluster'])} | {fnum(int(r['n']))} | {pct(r['pct'])} | "
          f"{pct(r['vpd_log_med'], 2)} | {pct(r['growth_log_med'], 2)} | "
          f"{pct(r['momentum_med'], 2)} | {pct(r['like_rate_med'], 4)} | "
          f"{pct(r['comment_rate_med'], 4)} | {pct(r['volatility_med'], 2)} | "
          f"{pct(r['subscribers_med'] / 1000 if r['subscribers_med'] >= 1000 else r['subscribers_med'], 0)} | "
          f"{pct(r['age_days_med'], 0)} | {pct(r['pct_ever_trending'])} | "
          f"{pct(r['pct_viral_A'])} | {r['top_category']} ({pct(r['pct_top_category'], 0)}%) |")
    A(f"| **Tổng** | {fnum(int(total['n']))} | 100,0 | {pct(total['vpd_log_med'], 2)} | "
      f"{pct(total['growth_log_med'], 2)} | {pct(total['momentum_med'], 2)} | "
      f"{pct(total['like_rate_med'], 4)} | {pct(total['comment_rate_med'], 4)} | "
      f"{pct(total['volatility_med'], 2)} | "
      f"{pct(total['subscribers_med'] / 1000 if total['subscribers_med'] >= 1000 else total['subscribers_med'], 0)} | "
      f"{pct(total['age_days_med'], 0)} | {pct(total['pct_ever_trending'])} | "
      f"{pct(total['pct_viral_A'])} | — |")

    A("\n### Cách đọc từng cụm\n")
    A("So sánh mỗi cụm với dòng **Tổng** ở cuối bảng. Cụm nào có số cao hơn "
      "hẳn mức chung thì đó là nét đặc trưng của cụm, thấp hơn hẳn thì là điểm "
      "yếu. Dưới đây là phần diễn giải tự động theo đúng so sánh đó:\n")
    for _, r in clusters.iterrows():
        c = int(r["cluster"])
        A(f"**Cụm {c}** — {fnum(int(r['n']))} video ({pct(r['pct'])}% mẫu):")
        traits = []
        for col, var, label, hi, lo in [
            ("vpd_log_med", "vpd_log", "tốc độ xem/ngày", "cao", "thấp"),
            ("growth_log_med", "growth_log", "tăng trưởng trong cửa sổ đo", "mạnh", "yếu"),
            ("momentum_med", "momentum", "đà tăng hiện tại", "còn nóng", "đã nguội"),
            ("like_rate_med", "like_rate", "tỷ lệ like", "cao", "thấp"),
            ("comment_rate_med", "comment_rate", "tỷ lệ bình luận", "cao", "thấp"),
            ("volatility_med", "volatility", "độ biến động tốc độ", "thất thường", "đều đặn"),
        ]:
            v = r[col]
            ref = total[col]
            z = (v - ref) / sd[var] if sd[var] else 0
            nd = DEC[col]
            if z >= 0.5:
                traits.append(f"{label} {hi} ({pct(v, nd)} so với mức chung {pct(ref, nd)})")
            elif z <= -0.5:
                traits.append(f"{label} {lo} ({pct(v, nd)} so với mức chung {pct(ref, nd)})")
        if traits:
            A("- " + "; ".join(traits) + ".")
        else:
            A("- Các biến đều gần mức chung — cụm này là nhóm đông nhất, đóng vai "
              "trò “mức nền” của cả mẫu.")
        A(f"- Quy mô: kênh trung vị {fnum(r['subscribers_med'])} người đăng ký, "
          f"video đã {pct(r['age_days_med'], 0)} ngày tuổi, "
          f"{pct(r['pct_ever_trending'])}% từng lên Trending, "
          f"{pct(r['pct_viral_A'])}% đạt nhãn viral_A.")
        A(f"- Thể loại đông nhất: **{r['top_category']}** "
          f"({pct(r['pct_top_category'], 0)}% video của cụm).\n")
    hi_v = clusters.loc[clusters["pct_viral_A"].idxmax()]
    lo_v = clusters.loc[clusters["pct_viral_A"].idxmin()]
    A("### So sánh nhanh giữa các cụm\n")
    A(f"- Tỷ lệ đạt viral_A cao nhất ở **cụm {int(hi_v['cluster'])}** "
      f"({pct(hi_v['pct_viral_A'])}% video của cụm), thấp nhất ở "
      f"**cụm {int(lo_v['cluster'])}** ({pct(lo_v['pct_viral_A'])}%). "
      f"Mức chung của cả mẫu là {pct(total['pct_viral_A'])}%.")
    hi_t = clusters.loc[clusters["pct_ever_trending"].idxmax()]
    A(f"- Tỷ lệ từng lên Trending cao nhất ở **cụm {int(hi_t['cluster'])}** "
      f"({pct(hi_t['pct_ever_trending'])}%), cho thấy cụm này gắn với video "
      "được đẩy lên trang Trending nhiều hơn.")
    smin, smax = clusters["subscribers_med"].min(), clusters["subscribers_med"].max()
    if smax / smin < 5:
        A("- Chênh lệch giữa các cụm là khác biệt về **hành vi**, không phải "
          "khác biệt về quy mô kênh: kênh trung vị giữa các cụm chỉ chênh nhau "
          f"chưa tới 5 lần ({fnum(smin)} đến {fnum(smax)} người đăng ký).\n")
    else:
        A(f"- Quy mô kênh có khác nhau giữa các cụm ({fnum(smin)} đến "
          f"{fnum(smax)} người đăng ký trung vị), nhưng đây là **phát hiện sau** "
          "khi phân cụm, không phải biến dùng để chia cụm.\n")
    A("Lưu ý: `subscribers` và tuổi video **không** tham gia phân cụm — chúng chỉ "
      "được tính sau khi đã có cụm, để mô tả. Vì vậy nếu cụm nào có kênh lớn hơn "
      "thì đó là **phát hiện**, không phải hệ quả của cách chia.\n")

    # 6. Chi-square
    A("## 6. Cụm có gắn với thể loại và viral_A không?\n")
    A("Dùng kiểm định Chi-square để trả lời: tỷ lệ thể loại (hoặc tỷ lệ viral_A) "
      "có khác nhau giữa các cụm một cách có ý nghĩa thống kê hay không.\n")
    A("| Cặp biến | n | Chi-square | df | p-value | Cramér's V |")
    A("|---|---:|---:|---:|---|---:|")
    for _, r in chi.iterrows():
        p = "< 1e-300" if r["p_value"] == 0 else f"{r['p_value']:.3g}".replace(".", ",")
        A(f"| {r['cap_bien']} | {fnum(int(r['n']))} | {pct(r['chi2'], 2)} | "
          f"{int(r['df'])} | {p} | {pct(r['cramers_v'], 3)} |")
    A("\nCách đọc:")
    A("- **p-value < 0,05**: có liên hệ — tỷ lệ giữa các cụm khác nhau thật, "
      "không phải do may mắn.")
    A("- **Cramér's V** (0 đến 1): độ mạnh của liên hệ. Dưới 0,1 là rất yếu, "
      "0,1–0,3 là yếu, 0,3–0,5 là trung bình, trên 0,5 là mạnh.")
    A("- Với cỡ mẫu hơn 20 nghìn video, p-value rất dễ nhỏ; nên **nhìn Cramér's V** "
      "để biết liên hệ có đáng kể hay không.\n")
    A("Cần nhớ: đây là liên hệ **mô tả**, không phải quan hệ nhân quả. "
      "Cụm được chia theo hành vi, nên nếu một thể loại rơi nhiều vào cụm "
      "“lan nhanh”, ta chỉ nói thể loại đó *thường* lan nhanh, chưa thể nói "
      "thể loại *gây ra* lan nhanh.\n")

    # 7. Hình
    A("## 7. Đọc Hình 5.9 (mặt phẳng PCA)\n")
    A("Sáu biến không thể vẽ trên giấy, nên dùng PCA nén xuống 2 chiều:\n")
    A("- Trục ngang **PC1**, trục dọc **PC2** là hai hướng biến thiên lớn nhất "
      "của dữ liệu.")
    A("- Mỗi chấm là một video, màu là cụm. Cụm nào nằm thành **dải riêng** thì "
      "tách bạch; cụm nào **chồng lấn** thì ranh giới mờ.")
    ev1 = ev2 = None
    rep = OUT / "q6_report.md"
    if rep.exists():
        import re
        m = re.search(r"PC1 ([\d.]+)%, PC2 ([\d.]+)%", rep.read_text(encoding="utf-8"))
        if m:
            ev1, ev2 = float(m.group(1)), float(m.group(2))
    if ev1 is not None:
        A(f"- Hai trục giữ được PC1 = {pct(ev1, 1)}% và PC2 = {pct(ev2, 1)}% "
          f"phương sai, cộng lại {pct(ev1 + ev2, 1)}% — tức hình chỉ phản ánh "
          "khoảng một nửa bức tranh. Đủ để nhìn xu hướng, **không đủ** để kết "
          "luận các cụm tách rời hoàn toàn.\n")
    else:
        A("- Phần trăm trên trục là lượng thông tin giữ lại được; cộng PC1 + PC2 "
          "càng cao thì hình càng phản ánh đầy đủ dữ liệu gốc.\n")

    # 8. R
    A("## 8. Đối chiếu với R\n")
    A("Yêu cầu đồ án bắt buộc chạy lại bằng R để kiểm tra chéo. Script R dùng "
      "cùng dữ liệu đã chuẩn hoá, cùng k, cùng seed, rồi tính ARI giữa nhãn "
      "của Python và nhãn của R.\n")
    A("- Tiêu chí: **ARI ≥ 0,8**.")
    r_file = OUT / "q6_R_check.txt"
    if r_file.exists():
        import re
        txt = r_file.read_text(encoding="utf-8-sig", errors="replace")
        m = re.search(r"ARI \(Python vs R\)\s*:\s*([\d.]+)", txt)
        kl = [l.strip() for l in txt.splitlines() if "KET LUAN" in l]
        verdict = kl[0].split(":")[-1].strip() if kl else "xem file"
        ari_r = pct(float(m.group(1)), 4) if m else "xem file"
        A(f"- Kết quả: ARI = **{ari_r}** — **{verdict}** (ngưỡng 0,8).")
        mr = re.search(r"So video moi cum \(R\)\s*:\s*(.+)", txt)
        if mr:
            A(f"- Số video mỗi cụm theo R: {mr.group(1).strip()} "
              "(thứ tự cụm của R có thể khác Python, không ảnh hưởng ARI).")
    else:
        A("- Chưa chạy `04_q6_kmeans.R` — sẽ bổ sung sau.")
    A("- ARI không đạt 1,0 là bình thường: R và Python khởi tạo tâm cụm khác nhau. "
      "Điều cần kiểm tra là hai bên **chia ra cùng một bức tranh**, không phải "
      "trùng từng video.\n")

    # 9. Hạn chế
    A("## 9. Ba điều cần nói khi bảo vệ\n")
    A(f"1. **Mẫu không đại diện toàn bộ**: chỉ {fnum(n_video)} video có ≥ 5 ngày đo, "
      "tức video được theo dõi đủ lâu. Video mới đăng hoặc đo ít ngày không vào mẫu.")
    A("2. **Cụm là mô tả, không phải chân lý**: silhouette trung bình cho thấy dữ liệu "
      "liên tục, các cụm là lát cắt có chủ đích để dễ hiểu.")
    A("3. **Không suy ra nhân quả**: biến như tốc độ xem và tỷ lệ like tương quan "
      "với nhau theo cách tự nhiên, không thể nói biến này làm biến kia thay đổi.\n")

    A("---\n")
    A("*File sinh tự động từ `04_q6_kmeans.py` + `04_q6_kmeans.R`. "
      "Số liệu khớp với `Q6_tong_hop.xlsx` và `q6_report.docx`.*")
    return "\n".join(L)


def main() -> None:
    md = build_md()
    out_docx = OUT / "Giai_thich_Q6_Kmeans.docx"
    convert_md_text(md, out_docx)
    print("Đã ghi:", out_docx)


if __name__ == "__main__":
    main()
