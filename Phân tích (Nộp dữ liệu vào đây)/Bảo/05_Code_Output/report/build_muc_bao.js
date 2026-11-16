// build_muc_bao.js - sinh Muc_Bao.docx từ report_data.json (do python/build_report_data.py tạo)
// Chạy:  python ../python/build_report_data.py && node build_muc_bao.js
// Ký hiệu trong chuỗi:  **đậm**   //nghiêng//   ⟦tô vàng = chỗ chờ số liệu / việc phải làm tay⟧
const fs = require("fs");
const path = require("path");
const D = require("docx");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, WidthType, ShadingType,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, VerticalAlign, PageBreak,
} = D;

const R = JSON.parse(fs.readFileSync(path.join(__dirname, "report_data.json"), "utf8"));
const OUT = path.join(__dirname, "Muc_Bao.docx");
const FIG = (p) => path.join(__dirname, "..", "outputs", p);
const FONT = "Times New Roman";
const W = 9121; // bề rộng nội dung (DXA) giống mẫu

// ------------------------------------------------------------------ helpers
function runs(text, base = {}) {
  // tách theo ⟦...⟧, **...**, //...//
  const out = [];
  const re = /(⟦[^⟧]*⟧|\*\*[^*]+\*\*|\/\/[^/]+\/\/)/g;
  text.split(re).forEach((tok) => {
    if (!tok) return;
    if (tok.startsWith("⟦")) out.push(new TextRun({ ...base, text: tok.slice(1, -1), highlight: "yellow" }));
    else if (tok.startsWith("**")) out.push(new TextRun({ ...base, text: tok.slice(2, -2), bold: true }));
    else if (tok.startsWith("//")) out.push(new TextRun({ ...base, text: tok.slice(2, -2), italics: true }));
    else out.push(new TextRun({ ...base, text: tok }));
  });
  return out;
}
const P = (t) => new Paragraph({ children: runs(t), indent: { firstLine: 432 }, spacing: { line: 360, before: 0, after: 0 }, alignment: AlignmentType.JUSTIFIED });
const PL = (t) => new Paragraph({ children: runs(t), spacing: { line: 360, before: 0, after: 0 }, alignment: AlignmentType.JUSTIFIED }); // không thụt đầu dòng
const B = (t) => new Paragraph({ children: runs(t), numbering: { reference: "bul", level: 0 }, spacing: { line: 360, before: 0, after: 0 }, alignment: AlignmentType.JUSTIFIED });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t })] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text: t })] });
const BEAT = (t) => new Paragraph({ children: [new TextRun({ text: t, bold: true })], keepNext: true, spacing: { before: 120, after: 0, line: 360 }, alignment: AlignmentType.LEFT });
const CAPT = (t) => new Paragraph({ style: "CaptionTable", children: runs(t, { italics: true, size: 22 }), spacing: { before: 60, after: 200, line: 276 }, keepLines: true });
const CAPF = (t) => new Paragraph({ style: "CaptionFigure", children: runs(t, { italics: true, size: 22 }), spacing: { before: 60, after: 200, line: 276 }, keepLines: true });
const GAP = () => new Paragraph({ children: [], spacing: { after: 0, line: 240 } });

const cellBorder = (c) => ({ top: { style: BorderStyle.SINGLE, size: 4, color: c }, bottom: { style: BorderStyle.SINGLE, size: 4, color: c }, left: { style: BorderStyle.SINGLE, size: 4, color: c }, right: { style: BorderStyle.SINGLE, size: 4, color: c } });
function cell(text, w, o = {}) {
  const head = !!o.head;
  const sz = o.sz || 22;
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    borders: cellBorder(head ? "45B0E1" : "A6A6A6"),
    shading: head ? { fill: "4C94D8", type: ShadingType.CLEAR, color: "auto" } : (o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined),
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: head ? AlignmentType.CENTER : (o.align || AlignmentType.LEFT),
      spacing: { line: 240 }, keepNext: !!o.keep,
      children: runs(String(text), head ? { bold: true, color: "FFFFFF", size: sz } : { size: sz, bold: !!o.bold }),
    })],
  });
}
// cols: [{w, align}] ; header: [..] ; rows: [[..]]
function table(widths, header, rows, o = {}) {
  const tot = widths.reduce((a, b) => a + b, 0);
  const aligns = o.aligns || widths.map((_, i) => (i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER));
  const sz = o.sz || 22;
  return new Table({
    width: { size: tot, type: WidthType.DXA }, columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: header.map((h, i) => cell(h, widths[i], { head: true, sz, keep: true })) }),
      ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, widths[i], { align: aligns[i], sz, bold: o.boldFirst && i === 0, keep: rows.length <= 8 })) })),
    ],
  });
}
function pngSize(file) { const b = fs.readFileSync(file); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
function figure(file, widthDxa = 8600, maxHeightDxa = 7600) {
  const [w, h] = pngSize(file);
  let wd = widthDxa, hd = Math.round((widthDxa * h) / w);
  if (hd > maxHeightDxa) { hd = maxHeightDxa; wd = Math.round((maxHeightDxa * w) / h); }
  const px = (d) => Math.round((d / 1440) * 96); // DXA -> pixel (96 dpi)
  return new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 0, line: 240, lineRule: "auto" },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: px(wd), height: px(hd) },
      altText: { title: path.basename(file), description: path.basename(file), name: path.basename(file) } })] });
}
function placeholderBox(text) {
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], rows: [new TableRow({ cantSplit: true, height: { value: 2600, rule: "atLeast" }, children: [new TableCell({
    width: { size: W, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    borders: { top: { style: BorderStyle.DASHED, size: 6, color: "7F7F7F" }, bottom: { style: BorderStyle.DASHED, size: 6, color: "7F7F7F" }, left: { style: BorderStyle.DASHED, size: 6, color: "7F7F7F" }, right: { style: BorderStyle.DASHED, size: 6, color: "7F7F7F" } },
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text, size: 22, highlight: "yellow" })] })] })] })] });
}

const S = R.scale, Q = R.dq, K = R.q3b_key, F = R.q3b_fit, M = R.q1_month;
const kids = [];
const add = (...x) => kids.push(...x);

const C30 = R.c30;

// ================================================================== 3.1
add(H2("3.1 Nguồn dữ liệu và cách thu thập"));
add(P("Dữ liệu được thu thập trực tiếp qua YouTube Data API v3, không dùng bộ dữ liệu có sẵn. Ba nhóm dữ liệu được lấy: (i) danh sách Trending của Việt Nam bằng videos.list với chart = mostPopular và regionCode = VN; (ii) danh sách video tải lên của từng kênh bằng playlistItems.list; (iii) thông tin kênh và số người đăng ký bằng channels.list. Việc dùng API chính thức giúp nguồn gốc số liệu minh bạch và truy vết được; đây cũng là nguồn mà chính YouTube dùng để công bố các chỉ số công khai như lượt xem và số người đăng ký (Google for Developers, n.d.)."));
add(P(`Script thu thập collect_youtube_v2.py chạy theo lịch run_all.bat và ghi bốn file thô: trending_snapshots.csv (danh sách Trending), video_tracking.csv (đo lại số liệu các video đang theo dõi), channel_history.csv (video tải lên của từng kênh) và channels_info.csv (thông tin và số người đăng ký của kênh). Trong các ngày có dữ liệu, số lượt thực tế mỗi ngày là ${R.perday.trending[0]}–${R.perday.trending[1]} lượt chụp Trending và ${R.perday.tracking[0]}–${R.perday.tracking[1]} lượt đo lại video. Dữ liệu thô gốc (4 file trước khi làm sạch, thu đến 12/11/2026) được sao lưu sang data_raw_20261112/, đặt chỉ đọc và lưu SHA-256 từng file trong checksums_raw.txt; các file đã làm sạch được sinh lại từ bản sao này bằng clean_data.py.`));
add(P(`Trong ${R.data_label}, nhật ký làm sạch ghi nhận **${Q.trending_runs} lần chụp Trending** trong ${Q.trending_ndays} ngày (trung bình ${Q.trend_per_day} lần mỗi ngày có dữ liệu), **${Q.tracking_runs} lượt đo lại video** trong ${Q.tracking_ndays} ngày và **${Q.history_runs} lượt lấy lịch sử kênh** trong ${Q.history_ndays} ngày (${Q.history_ranges}). Giai đoạn theo dõi chính thức kéo dài 22 ngày, từ 22/10 đến 12/11/2026; lần đo cuối cùng trong dữ liệu được ghi lúc ${S.last_collect_vn} ngày ${S.last_collect_date} (giờ Việt Nam). Theo kiểm tra trong collection_summary.csv, Trending không có dữ liệu các ngày ${R.missing.trending}; đo lại video (tracking) không có dữ liệu các ngày ${R.missing.tracking}. Lịch sử kênh (history) không được lấy hằng ngày mà chỉ vào các ngày ${Q.history_ranges}. Nhật ký làm sạch còn cảnh báo vài khoảng cách 10–60 phút giữa hai lô liên tiếp (một ở tracking, hai ở history) đang được tính là hai lượt chạy riêng, nên số lượt chạy có thể bị đếm dư nếu đó thực chất là một lượt bị ngắt; điều này chỉ ảnh hưởng đến số lượt chạy được đếm, không ảnh hưởng đến các lần đo. Nguyên nhân các ngày thiếu không được ghi lại trong dữ liệu thu thập. Vì danh sách Trending và số liệu đo lại là số liệu tại thời điểm chụp nên không thể thu bù cho các ngày này, và các ngày này không được điền bù trong dữ liệu đã làm sạch.`));
add(P("Các nguồn dữ liệu của đồ án được tóm tắt trong Bảng 3.1; lịch nghỉ lễ và Tết do nhóm tự tổng hợp từ thông báo nghỉ lễ chính thức của cơ quan nhà nước (holidays_vn.csv, Khôi phụ trách)."));
add(table([2900, 3300, 2921], ["Nguồn", "Biến số / dữ liệu", "Ghi chú"], [
  ["YouTube Data API v3 (videos.list, chart = mostPopular, regionCode = VN)", "Thứ hạng thịnh hành, lượt xem, lượt thích, bình luận, độ dài, thể loại, số thẻ tag, thời điểm đăng", "API chính thức của Google; hạn mức mặc định 10.000 đơn vị mỗi ngày"],
  ["YouTube Data API v3 (playlistItems.list, channels.list)", "Video lịch sử và số người đăng ký của nhóm kênh", "Nhóm đối chứng không thịnh hành; chi phí 1 đơn vị mỗi lần gọi"],
  ["Google Trends (pytrends hoặc tải thủ công)", "Mức độ quan tâm theo từ khóa theo tuần", "Đối chiếu xu hướng (Mục 3.6) và biến ngoại sinh cho ARIMAX"],
  ["Lịch nghỉ lễ, Tết Việt Nam", "Biến giả ngày lễ, kỳ nghỉ (holidays_vn.csv)", "Tự tổng hợp từ lịch nghỉ lễ chính thức, mỗi dòng có nguồn"],
], { aligns: [AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT] }));
add(CAPT("Bảng 3.1. Nguồn dữ liệu của đồ án"));
add(P("Dữ liệu sau làm sạch gồm năm file, mô tả trong Bảng 3.2. Từ ngày 13/11/2026, mọi con số trong báo cáo chỉ lấy từ thư mục data_final_20261113."));
add(table([2600, 6521], ["File", "Nội dung"], [
  ["videos_master.csv", "Mỗi dòng một video, số liệu của lần đo mới nhất (55 cột)"],
  ["measurements.csv", "Mỗi dòng một lần đo; cột is_last_of_day đánh dấu lần đo cuối mỗi ngày"],
  ["trending_clean.csv", "Mỗi dòng một video trong một lần chụp Trending"],
  ["channels_latest.csv", "Mỗi dòng một kênh, số liệu mới nhất"],
  ["dq_report.txt", "Báo cáo chất lượng dữ liệu sinh tự động khi làm sạch"],
], { aligns: [AlignmentType.LEFT, AlignmentType.LEFT] }));
add(CAPT("Bảng 3.2. Các file dữ liệu sau làm sạch (nguồn: data_final_20261113/, dq_report.txt)"));
add(P(`Quy mô dữ liệu (${R.data_label})${R.is_final ? "" : " ⟦(số tạm, thay bằng dữ liệu chốt)⟧"}: **${S.n_video} video** của **${S.n_channels} kênh**, trong đó **${S.n_trending_videos} video** từng lọt Trending; **${S.n_meas} lần đo**; **${S.n_trending_rows} dòng** Trending từ ${S.n_trending_snap} lần chụp. Bối cảnh: theo số liệu Google do Tuoi Tre News (2026) dẫn lại, YouTube tiếp cận khoảng 93% người dùng internet Việt Nam mỗi ngày, và DataReportal (2026) ghi nhận 85,6 triệu người dùng internet tại Việt Nam vào tháng 10/2025, nên đây là nền tảng có quy mô đủ lớn để các câu hỏi của đồ án có ý nghĩa thực tiễn.`));

// ================================================================== 3.2
add(H2("3.2 Làm sạch dữ liệu"));
add(P("Quy trình làm sạch do clean_data.py thực hiện và ghi kết quả vào dq_report.txt. Bảng 3.2b liệt kê từng bước cùng số dòng bị tác động, lấy trực tiếp từ dq_report.txt và từ các file sạch."));
add(table([600, 3200, 1500, 3821], ["Bước", "Nội dung", "Số dòng", "Cách xử lý"], [
  ["1", "Đọc dữ liệu thô", `${Q.trend_raw} / ${Q.track_raw} / ${Q.hist_raw} / ${Q.chan_raw}`, "Lần lượt: trending_snapshots, video_tracking, channel_history, channels_info"],
  ["2", "video_id bị hỏng (#NAME?)", `${Q.bad_id}`, `Khôi phục ${Q.fixed_id}/${Q.bad_id} dòng qua (channel_id, published_at); không loại dòng nào`],
  ["3", "Tiêu đề, tên kênh mất dấu tiếng Việt", `${Q.title_suspect} nghi hỏng`, `Thay bằng bản đúng từ video_tracking/channel_history cho ${Q.trend_raw}/${Q.trend_raw} dòng Trending`],
  ["4a", "Lượt thích lớn hơn lượt xem", `${Q.lk_gt}`, "Đặt likes = NaN (nhiễu API / video mới)"],
  ["4b", "Bình luận lớn hơn lượt xem", `${Q.cm_gt}`, "Đặt comments = NaN"],
  ["4c", "Lượt xem bằng 0", `${Q.v0}`, "Giữ trong measurements; loại khỏi phân tích log và tỷ lệ"],
  ["4d", "Lượt xem rỗng (NaN)", `${Q.vnan}`, "Loại dòng đo"],
  ["4e", "Lượt xem giảm giữa hai lần đo liên tiếp", `${Q.dec} / ${Q.pairs} cặp`, "Dùng cummax để chuỗi đơn điệu"],
  ["4f", "Kết quả gộp bảng lần đo", `${S.n_meas} lần đo`, `Của ${S.n_video} video`],
  ["5", "Bảng kênh", `${S.n_channels} kênh`, `Lấy bản ghi mới nhất từ ${Q.chan_raw} dòng lịch sử`],
  ["6", "Bảng video master", `${S.n_video} video`, "Không video nào thiếu thông tin kênh"],
  ["7", "Quần thể phân tích H (Mục 4.1)", `${S.n_H} video`, `Loại ${S.n_excl} video khỏi master (các lý do chồng lấn nhau)`],
], { sz: 20, aligns: [AlignmentType.CENTER, AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.LEFT] }));
add(CAPT("Bảng 3.2b. Các bước làm sạch và số dòng bị tác động (nguồn: dq_report.txt, outputs/reliability/reliability_table.csv)"));
add(P(`Trong ${S.n_excl} video không thuộc H, có ${S.n_not_hist} video không có trong lịch sử kênh (in_history = FALSE), ${S.n_live} video đang phát trực tiếp hoặc chưa phát (is_live_or_upcoming = TRUE), ${R.excl.views0} video có lượt xem bằng 0 và ${R.excl.age_lt1} video có tuổi dưới 1 ngày; một video có thể rơi vào nhiều nhóm nên các số không cộng thành tổng. Quần thể H còn **${S.n_H} video** từ **${S.n_ch_H} kênh**.`));
add(P(`Các file CSV được đọc với encoding utf-8-sig và video_id đọc dưới dạng chuỗi. Các cột pub_* đã ở giờ Việt Nam (UTC+7); phép kiểm tra đối chiếu pub_hour với published_ts đổi sang UTC+7 cho kết quả khớp ${R.pub_hour_match}%. Số lượt thích và bình luận rỗng (do ẩn hoặc tắt) được giữ là NaN, các tỷ lệ like_rate và comment_rate chỉ tính khi giá trị không rỗng.`));

// ================================================================== 3.3

// Làm gọn Bảng 3.3 khi dựng báo cáo (CSV gốc giữ nguyên để đối chiếu dq_report)
const relRows = R.rel.filter((r) => !/theo dq_report/.test(r.tc)).map((r) => {
  let tc = r.tc, how = r.how;
  tc = tc.replace(/\(dưới ([0-9.]+)\)/, (m, v) => `(log10 lượt xem dưới ${v.replace(".", ",")})`)
         .replace(/\(trên ([0-9.]+)\)/, (m, v) => `(log10 lượt xem trên ${v.replace(".", ",")})`)
         .replace("(tính lại từ views_raw)", "(tính lại từ views_raw; khớp dq_report.txt)");
  if (/phải bằng 0|Phải bằng 0/.test(how)) {
    how = how.startsWith("Phải") ? "Đạt: không còn dòng nào sau làm sạch" : "Không có dòng trùng; đã loại khi làm sạch và kiểm tra lại trên file sạch";
  }
  return Object.assign({}, r, { tc, how });
});
add(H2("3.3 Chất lượng dữ liệu và tính nhất quán logic"));
add(P("Độ tin cậy của dữ liệu được chứng minh qua 6 tiêu chí: (1) nguồn gốc minh bạch (API chính thức của Google); (2) chất lượng dữ liệu (xử lý giá trị thiếu, trùng lặp, ngoại lai); (3) tính nhất quán logic (lượt thích và bình luận không vượt quá lượt xem, lượt xem không giảm giữa hai lần đo); (4) đối chiếu ngẫu nhiên với số liệu hiển thị trên YouTube (Mục 3.4); (5) đối chiếu xu hướng với nguồn độc lập là Google Trends (Mục 3.6); (6) nêu rõ các hạn chế (Mục 3.5). Tiêu chí (2) và (3) được kiểm tra bằng Bảng 3.3; mỗi dòng nêu số đếm, tỷ lệ và cách xử lý. Số liệu lấy từ reliability_table.csv."));
add(table([3000, 1050, 1050, 4021], ["Tiêu chí", "Số đếm", "Tỷ lệ (%)", "Cách xử lý"],
  relRows.map((r) => [r.tc, r.cnt, r.pct, r.how]), { sz: 19, aligns: [AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.LEFT] }));
add(CAPT(`Bảng 3.3. Kết quả kiểm tra chất lượng và tính nhất quán logic (nguồn: outputs/reliability/reliability_table.csv). Mẫu số: số video (${S.n_video}) cho các dòng về cờ rỗng, trùng video và ngoại lai; số lần đo cho các dòng còn lại`));
add(P(`Kết quả cho thấy dữ liệu đạt yêu cầu cho phân tích. Về giá trị rỗng, ${R.rel[0].pct}% video ẩn lượt thích và ${R.rel[1].pct}% tắt bình luận; các video này được giữ lại nhưng không đưa vào tỷ lệ. Không phát hiện video trùng hay lần đo trùng trong các file sạch. Về ngoại lai, ${R.rel[6].cnt} video (${R.rel[6].pct}%) nằm dưới và ${R.rel[7].cnt} video (${R.rel[7].pct}%) nằm trên ngưỡng IQR của log_views; nhóm chọn giữ lại vì đây là video thật và phân phối lượt xem của nền tảng vốn có đuôi dài, thay vào đó dùng log10 và lv_adj để giảm ảnh hưởng.`));
add(P(`Về tính nhất quán logic, ${Q.lk_gt} dòng có lượt thích lớn hơn lượt xem và ${Q.cm_gt} dòng có bình luận lớn hơn lượt xem trước khi làm sạch; sau khi đặt NaN, kiểm tra lại cho kết quả bằng 0. Lượt xem giảm giữa hai lần đo liên tiếp ở ${Q.dec} trên ${Q.pairs} cặp (**${Q.pct_true}%**); tự tính lại từ cột views_raw cho đúng số này. Hiện tượng này phù hợp với cách YouTube vận hành: hệ thống có thể tạm làm chậm, đóng băng hoặc điều chỉnh số đếm và loại các lượt phát kém chất lượng khi xác thực (YouTube Help, n.d.). Vì vậy nhóm dùng cummax để chuỗi lượt xem không giảm. Lượt thích giảm ở ${R.rel[R.rel.length - 1].pct}% cặp, được giữ nguyên vì người xem có thể bỏ thích.`));

// ================================================================== 3.4
add(H2("3.4 Đối chiếu ngẫu nhiên 30 video với YouTube"));
add(P(`Để kiểm tra số liệu API có khớp số hiển thị trên YouTube, nhóm chọn 30 video theo phân tầng lượt xem từ lần đo gần nhất: 10 video dưới 10 nghìn lượt, 10 video từ 10 nghìn đến 1 triệu lượt và 10 video trên 1 triệu lượt (random_state = 42, script pick30.py). Chỉ các video có lần đo trong 6 giờ cuối của lần thu cuối, đang công khai bình thường và đủ lượt thích, bình luận mới được đưa vào danh sách chọn để giờ chênh giữa hai lần đọc chỉ vài chục phút. ${C30 ? `Sau lần thu cuối, nhóm mở từng video trên YouTube lúc ${C30.t_first}–${C30.t_last} ngày ${C30.t_date} (giờ Việt Nam), tức cách lần đo API ${C30.lag_min}–${C30.lag_max} phút, và ` : `Sau lần thu cuối ngày 12/11 lúc 20:00, nhóm mở từng video trên YouTube trong vòng khoảng 90 phút, `}ghi số lượt xem, thích, bình luận và giờ xem; nhóm không lưu ảnh chụp màn hình, mọi số được ghi trực tiếp vào reliability_check_30videos.csv. Sai lệch tương đối được tính bằng (YouTube − API) / API, kèm giờ chênh của từng dòng.`));
add(P(C30
  ? `Kết quả: trung vị sai lệch tương đối là **${C30.med_views}** với lượt xem, ${C30.med_likes} với lượt thích và ${C30.med_comments} với bình luận; sai lệch tuyệt đối lớn nhất của lượt xem là ${C30.max_views}. Lượt xem trên YouTube trùng hoàn toàn với API ở ${C30.n_exact_views}/30 video, lượt thích ở ${C30.n_exact_likes}/30 và bình luận ở ${C30.n_exact_comments}/30 video (tính cả các trường hợp hai bên cùng bằng 0; nếu chỉ tính video có số đếm API khác 0 thì lượt thích là ${C30.n_exact_likes_nonzero}/${C30.n_nonzero_likes} và bình luận là ${C30.n_exact_comments_nonzero}/${C30.n_nonzero_comments}). Có ${C30.share_pos}% video mà lượt xem trên YouTube cao hơn API, phù hợp với việc lượt xem tiếp tục tăng trong ${C30.lag_min}–${C30.lag_max} phút giữa hai lần đọc; ${C30.n_neg_views} video có lượt xem thấp hơn API, có thể do YouTube điều chỉnh số đếm khi xác thực (YouTube Help, n.d.). Với chỉ 10 video mỗi tầng, đây là phép kiểm tra tính hợp lý chứ không phải ước lượng chính xác sai số của API.`
  : "⟦Kết quả: trung vị sai lệch lượt xem […], lượt thích […], bình luận […]. [Bảo: điền sau khi chạy pick30.py --summarize trên dữ liệu 12/11. Xác nhận bằng cột giờ chênh rằng sai lệch dương chủ yếu do thời gian trôi giữa lần đo API và lần xem trên YouTube.]⟧"));
add(C30 ? table([2200, 1100, 1500, 1500, 1500, 1321], ["Nhóm", "Số video", "TV sai lệch lượt xem", "TV sai lệch lượt thích", "TV sai lệch bình luận", "Giờ chênh TV (phút)"], C30.rows, { sz: 20 })
  : table([2200, 1100, 1500, 1500, 1500, 1321], ["Nhóm", "Số video", "TV sai lệch lượt xem", "TV sai lệch lượt thích", "TV sai lệch bình luận", "Giờ chênh TV (phút)"], [
  ["< 10 nghìn", "10", "⟦[…]⟧", "⟦[…]⟧", "⟦[…]⟧", "⟦[…]⟧"],
  ["10 nghìn – 1 triệu", "10", "⟦[…]⟧", "⟦[…]⟧", "⟦[…]⟧", "⟦[…]⟧"],
  ["> 1 triệu", "10", "⟦[…]⟧", "⟦[…]⟧", "⟦[…]⟧", "⟦[…]⟧"],
  ["Chung", "30", "⟦[…]⟧", "⟦[…]⟧", "⟦[…]⟧", "⟦[…]⟧"],
], { sz: 20 }));
add(CAPT("Bảng 3.4. Kết quả đối chiếu 30 video (nguồn: outputs/reliability/reliability_check_30videos.csv)"));

// ================================================================== 3.5
add(H2("3.5 Hạn chế của dữ liệu và các điều chỉnh"));
add(B(`**Thời gian theo dõi ngắn:** kế hoạch là 22 ngày (22/10–12/11/2026) thay vì tối thiểu 8 tuần trong đề cương; thực tế có ${S.n_days} ngày có số đo do đo lại video (tracking) thiếu các ngày ${R.missing.tracking}. Các chuỗi dựa trên dữ liệu theo dõi (N1, N2) vì vậy chỉ có tối đa ${S.n_days} điểm theo ngày nên chỉ mang tính minh họa.`));
add(B(`**Giới hạn 500 video mỗi kênh:** script chỉ lấy tối đa 500 video mới nhất của mỗi kênh mỗi lần lấy lịch sử, nên số video theo tháng không phản ánh xu hướng đăng thực của kênh. Có ${S.n_ch_ge500} kênh có từ 500 video lịch sử trở lên (nhiều nhất ${S.max_ch_hist} video, có thể do các lượt lấy lịch sử ở những ngày khác nhau cộng dồn), và ${S.n_ch_lt500} kênh có dưới 500. Chuỗi S1 chỉ dùng các kênh có dưới 500 video.`));
add(B("**Số người đăng ký đo lúc thu thập,** không phải lúc video được đăng, và API trả về giá trị làm tròn xuống ba chữ số có nghĩa (Google for Developers, n.d.). Biến log_subs vì thế chỉ phản ánh quy mô kênh hiện tại và có sai số làm tròn."));
add(B(`**Quy mô và cách chọn mẫu kênh:** số kênh thực tế là ${S.n_channels}, trong đó ${S.n_ch_hist} kênh có video trong lịch sử (và tạo nên quần thể H) và ${S.n_ch_no_hist} kênh chỉ xuất hiện qua danh sách Trending. Con số này cao hơn dự kiến 150–200 kênh của đề cương. Mẫu kênh không phải mẫu ngẫu nhiên của toàn bộ YouTube Việt Nam, trong khi Tuoi Tre News (2026) cho biết Việt Nam có hơn 180.000 kênh trên 10.000 người đăng ký, nên kết quả chỉ nên hiểu cho nhóm kênh được theo dõi.`));
add(B(`**Chênh lệch giữa các kênh lớn:** ở Mục 5.1, ${R.q1_between_share}% phương sai của lv_adj nằm giữa các kênh, nên mọi so sánh giữa nhóm video (theo giờ, thể loại…) đều lẫn với khác biệt giữa các kênh.`));
add(B(`**Phủ đo lại không đều:** theo dq_report.txt, chỉ ${Q.ge2} video có từ 2 lần đo và ${Q.ge5} video có từ 5 lần đo, nên các phân tích dùng chuỗi đo (Q6) chỉ áp dụng cho nhóm video nhỏ này.`));
add(B(`**Ngày thiếu lượt thu:** Trending thiếu các ngày ${R.missing.trending}; tracking thiếu các ngày ${R.missing.tracking}; lịch sử kênh chỉ được lấy vào ${Q.history_ranges}. Nguyên nhân các ngày thiếu không được ghi lại và các ngày này không được điền bù (xem Mục 3.1).`));

// ================================================================== 5.1
add(H2("5.1 Q1: Thống kê mô tả"));
add(BEAT("Phương pháp."));
add(B("Bảng thống kê gồm n, trung bình, trung vị, độ lệch chuẩn (mẫu, n − 1), hệ số biến thiên (CV = độ lệch chuẩn / trung bình), độ lệch và độ nhọn dư (tính theo mô-men, không hiệu chỉnh mẫu) của lượt xem, lượt thích, bình luận ở giá trị gốc và log10, tách video ngắn (từ 60 giây trở xuống) và video dài. Với lượt thích và bình luận, log10 chỉ tính trên giá trị lớn hơn 0 và các giá trị rỗng (ẩn hoặc tắt) được bỏ qua."));
add(B("Trung vị lv_adj và like_rate theo giờ đăng (pub_hour), thứ (pub_dow) và năm-tháng của pub_date_vn."));
add(B("Heatmap giờ × thứ của trung vị lv_adj; ô có dưới 30 video để trống."));
add(B("Boxplot lv_adj theo 10 thể loại có nhiều video nhất."));
add(B("Kiểm tra độ vững (bổ sung): trừ trung vị lv_adj của chính kênh khỏi lv_adj của từng video, để tách khác biệt do //kênh nào// đăng khỏi khác biệt do //giờ hoặc thứ// đăng."));
add(B("Không dùng số video theo tháng để nói về xu hướng vì mỗi kênh chỉ lấy tối đa 500 video mới nhất. Mọi so sánh dùng lv_adj, không dùng lượt xem thô."));
add(BEAT("Kết quả và mức ý nghĩa."));
add(P(`Cỡ mẫu: n_H = **${S.n_H}** video từ **${S.n_ch_H}** kênh (${R.data_label}). Đây là thống kê mô tả nên không có kiểm định giả thuyết; “mức ý nghĩa” ở đây là độ lớn của các khác biệt.`));
const hdr8 = ["Biến", "n", "Trung bình", "Trung vị", "Độ lệch chuẩn", "CV", "Độ lệch", "Độ nhọn"];
add(table([1900, 900, 1150, 1000, 1250, 750, 1000, 1171], hdr8, R.q1_all, { sz: 19, aligns: [AlignmentType.LEFT, ...Array(7).fill(AlignmentType.RIGHT)] }));
add(CAPT("Bảng 5.1. Thống kê mô tả lượt xem, lượt thích, bình luận (nguồn: outputs/q1/q1_descriptive_table.csv)"));
add(P(`Lượt xem phân bố lệch phải rất mạnh: trung bình ${R.q1_all[0][2]} lượt nhưng trung vị chỉ ${R.q1_all[0][3]} lượt, CV bằng ${R.q1_all[0][5]}, độ lệch ${R.q1_all[0][6]} và độ nhọn dư ${R.q1_all[0][7]}. Sau khi lấy log10, độ lệch giảm còn ${R.q1_all[1][6]} và độ nhọn dư còn ${R.q1_all[1][7]}, tức gần đối xứng; đây là lý do mọi phân tích sau đó dùng log10 và lv_adj. Lượt thích và bình luận có hình dạng tương tự; số quan sát của log10 nhỏ hơn vì chỉ tính giá trị lớn hơn 0 (${R.q1_all[3][1]} video có lượt thích và ${R.q1_all[5][1]} video có bình luận khác 0).`));
const split = [];
for (let i = 0; i < 6; i++) { const a = R.q1_short[i], b = R.q1_long[i]; split.push([a[0], "Ngắn", a[1], a[2], a[3], a[4], a[5]]); split.push([b[0], "Dài", b[1], b[2], b[3], b[4], b[5]]); }
add(table([2000, 750, 900, 1450, 1250, 1450, 1321], ["Biến", "Nhóm", "n", "Trung bình", "Trung vị", "Độ lệch chuẩn", "CV"], split, { sz: 18, aligns: [AlignmentType.LEFT, AlignmentType.CENTER, ...Array(5).fill(AlignmentType.RIGHT)] }));
add(CAPT("Bảng 5.1b. Thống kê mô tả tách video ngắn (≤ 60 giây) và video dài (nguồn: outputs/q1/q1_descriptive_table.csv)"));
add(P(`Video ngắn có trung vị lượt xem thấp hơn video dài (${R.q1_short[0][3]} so với ${R.q1_long[0][3]}) nhưng trung bình cao hơn (${R.q1_short[0][2]} so với ${R.q1_long[0][2]}), nghĩa là số ít video ngắn rất thành công kéo trung bình lên. Ở lượt thích, trung bình của video ngắn (${R.q1_short[2][2]}) gấp khoảng ${R.q1_like_mean_ratio} lần video dài (${R.q1_long[2][2]}) trong khi trung vị chênh ít hơn nhiều (${R.q1_short[2][3]} và ${R.q1_long[2][3]}); trung vị bình luận của video ngắn (${R.q1_short[4][3]}) thấp hơn video dài (${R.q1_long[4][3]}).`));
add(figure(FIG("q1/q1_by_hour.png")));
add(CAPF("Hình 5.1. Trung vị lv_adj theo giờ đăng; đường đứt đỏ là trung vị sau khi trừ trung vị của kênh (nguồn: outputs/q1/q1_by_hour.png)"));
const t = R.q1_sum, ht = R.q1_hour_top, hb = R.q1_hour_bot;
add(P(`**Theo giờ đăng.** Trung vị lv_adj cao nhất lúc ${ht[0][0]}h (${ht[0][2]}, n = ${ht[0][1]}) và thấp nhất lúc ${hb[0][0]}h (${hb[0][2]}, n = ${hb[0][1]}); khoảng cách ${t.hour_range.slice(0, 5).replace(".", ",")} đơn vị log10, tức khoảng ${R.q1_hour_range_ratio} lần về lượt xem đã chuẩn hóa tuổi. Tuy nhiên, sau khi trừ trung vị của chính kênh, khoảng cách này co lại còn ${t.hour_range_within_channel.slice(0, 5).replace(".", ",")} (khoảng ${R.q1_within_ratio} lần), với giá trị cao nhất lúc ${R.q1_hour_within_max[0]}h (${R.q1_hour_within_max[1]}) và thấp nhất lúc ${R.q1_hour_within_min[0]}h (${R.q1_hour_within_min[1]}). Cùng lúc đó, ${R.q1_between_share}% phương sai của lv_adj nằm giữa các kênh. Như vậy phần lớn chênh lệch theo giờ trong hình là do những kênh có sẵn nhiều người xem hay đăng vào giờ nào, chứ không phải do bản thân giờ đăng. Tỷ lệ thích (trung vị like_rate) dao động từ ${R.q1_like_rate_range[0]}% đến ${R.q1_like_rate_range[1]}% giữa các giờ.`));
add(table([2300, 1200, 1900, 2200, 1521], ["Thứ đăng", "n", "Trung vị lv_adj", "Trung vị lv_adj (trừ kênh)", "Trung vị like_rate (%)"], R.q1_dow, { sz: 20, aligns: [AlignmentType.LEFT, ...Array(4).fill(AlignmentType.CENTER)] }));
add(CAPT("Bảng 5.1c. Trung vị lv_adj và like_rate theo thứ đăng (nguồn: outputs/q1/q1_by_dow.csv)"));
add(P(`**Theo thứ đăng.** Trung vị lv_adj dao động rất hẹp, khoảng cách lớn nhất giữa các thứ chỉ ${t.dow_range.slice(0, 5).replace(".", ",")} (khoảng ${R.q1_dow_ratio} lần) và còn ${t.dow_range_within_channel.slice(0, 5).replace(".", ",")} sau khi trừ trung vị của kênh. ${R.q1_dow_hi_gt_lo ? `Thứ Sáu đến Chủ nhật (${R.q1_dow_hi[0]} đến ${R.q1_dow_hi[1]}) cao hơn nhẹ so với Thứ Hai đến Thứ Năm (${R.q1_dow_lo[0]} đến ${R.q1_dow_lo[1]}), ` : ``}còn tỷ lệ thích gần như không đổi theo thứ (từ ${R.q1_dow.map((r) => r[4]).sort()[0]}% đến ${R.q1_dow.map((r) => r[4]).sort().slice(-1)[0]}%).`));
add(P(`**Theo tháng đăng.** Trung vị lv_adj theo năm-tháng (từ ${M.first} đến ${M.last}) nằm trong khoảng từ ${R.q1_month_rng[0]} đến ${R.q1_month_rng[1]} (outputs/q1/q1_by_month.csv). Số video mỗi tháng thay đổi từ ${M.n_min} đến ${M.n_max} (tháng 2026-10 có ${M.n_last_full} video), có thể phản ánh giới hạn 500 video mỗi kênh và thời điểm thu thập chứ không phản ánh lượng đăng thực, nên nhóm không diễn giải xu hướng theo tháng và không dùng số video theo tháng để nói về xu hướng.`));
add(figure(FIG("q1/q1_heatmap.png"), 7600, 6900));
add(CAPF("Hình 5.2. Heatmap trung vị lv_adj theo giờ và thứ đăng (nguồn: outputs/q1/q1_heatmap.png)"));
add(P(`Cả ${t.cells_total} ô giờ × thứ đều có từ 30 video trở lên (${t.cells_blank} ô bị để trống). ${R.q1_heat.hour_dominant ? `Nếu lấy trung bình theo từng hàng (giờ) rồi so giờ cao nhất với giờ thấp nhất thì chênh ${R.q1_heat.hour_rng} đơn vị log10; làm tương tự theo từng cột (thứ) thì chỉ chênh ${R.q1_heat.dow_rng}. Mức nổi trội vì vậy gắn với giờ nhiều hơn gắn với thứ, phù hợp với nhận xét ở trên về cơ cấu kênh.` : `Trung bình theo hàng (giờ) dao động ${R.q1_heat.hour_rng} và theo cột (thứ) ${R.q1_heat.dow_rng}.`} Ô cao nhất là ${t.cell_best} và ô thấp nhất là ${t.cell_worst}; ô cao nhất có cỡ mẫu nhỏ nên không nên diễn giải riêng.`));
add(figure(FIG("q1/q1_box_category.png")));
add(CAPF("Hình 5.3. Phân bố lv_adj theo 10 thể loại có nhiều video nhất (nguồn: outputs/q1/q1_box_category.png, q1_by_category.csv)"));
add(P(`**Theo thể loại.** Trong 10 thể loại đông nhất, trung vị lv_adj thô cao nhất ở ${t.cat_best} (${R.q1_cat.find((r) => r[0] === t.cat_best)[2]}, n = ${R.q1_cat.find((r) => r[0] === t.cat_best)[1]}) và thấp nhất ở ${t.cat_worst} (${R.q1_cat.find((r) => r[0] === t.cat_worst)[2]}, n = ${R.q1_cat.find((r) => r[0] === t.cat_worst)[1]}); khoảng cách ${t.cat_range_top10.slice(0, 5).replace(".", ",")} đơn vị log10 (khoảng ${R.q1_cat_ratio} lần). Tuy nhiên sau khi trừ trung vị của chính kênh, khoảng cách giữa 10 thể loại này chỉ còn ${R.q1_cat_within_range} đơn vị log10 (khoảng ${R.q1_cat_within_ratio} lần), nhỏ hơn khoảng cách theo giờ trong cùng kênh (${t.hour_range_within_channel.slice(0, 5).replace(".", ",")} đơn vị log10), và thứ hạng đảo lại: cao nhất là ${t.cat_best_within}, thấp nhất là ${t.cat_worst_within}. Vì vậy chênh lệch thô theo thể loại chủ yếu phản ánh việc thể loại nào tập trung nhiều kênh lớn, không phải bản thân thể loại; nhiều cặp thể loại vẫn có hộp chồng lấn.`));
add(BEAT("Giải thích thực tiễn."));
add(P(`Kết quả cho thấy khác biệt lớn nhất trong dữ liệu là khác biệt giữa các kênh; chênh lệch thô theo thể loại phần lớn cũng phản ánh cơ cấu kênh, còn thời điểm đăng chỉ có liên quan yếu khi so sánh trong cùng một kênh. Điều này phù hợp với bối cảnh nền tảng: YouTube tiếp cận khoảng 93% người dùng internet Việt Nam mỗi ngày (Tuoi Tre News, 2026) trong một thị trường có 85,6 triệu người dùng internet (DataReportal, 2026), tức là các video cạnh tranh để được xem trên một nền tảng rất lớn. Trong dữ liệu của nhóm, lượt xem phân bố rất không đều: trung bình bằng khoảng ${R.q1_views_mean_over_median} lần trung vị, do một số ít video có lượt xem rất cao kéo trung bình lên. Cần nhớ lượt xem công khai không phải số đếm tuyệt đối: YouTube có thể tạm làm chậm, đóng băng hoặc điều chỉnh số đếm để xác thực (YouTube Help, n.d.), vì vậy các so sánh nên dựa trên lv_adj đã chuẩn hóa tuổi video và các khác biệt nhỏ nên được đọc thận trọng.`));
add(BEAT("Khuyến nghị."));
add(B(`Nhà sáng tạo không nên chọn giờ đăng chỉ dựa trên trung vị theo giờ của toàn bộ nền tảng: chênh lệch khoảng ${R.q1_hour_range_ratio} lần giữa các giờ phần lớn đến từ việc kênh nào đăng, và khi so trong cùng kênh chỉ còn khoảng ${R.q1_within_ratio} lần. Khuyến nghị an toàn hơn là thử các khung giờ khác nhau trong chính kênh của mình và so lv_adj hoặc lượt xem theo tuổi video.`));
add(B(`Không cần dồn lịch đăng vào cuối tuần chỉ vì trung vị cao hơn: khoảng cách giữa các thứ rất nhỏ (khoảng ${R.q1_dow_ratio} lần) và còn khoảng ${R.q1_dow_within_ratio} lần khi so trong cùng kênh.`));
add(B("Nhãn hàng và MCN nên coi kênh là yếu tố có liên quan rõ nhất tới lượt xem; thể loại vẫn hữu ích để chọn đối tượng mục tiêu nhưng phần lớn chênh lệch thô theo thể loại là do kênh, còn giờ đăng chỉ nên tinh chỉnh sau cùng trong chính kênh đã chọn. Có thể dùng tỷ lệ thích trung vị (khoảng 1% lượt xem) làm mốc tham chiếu về mức tương tác."));
add(BEAT("Hạn chế."));
add(B("Số video theo tháng không phản ánh xu hướng đăng thật do giới hạn 500 video mỗi kênh (Mục 3.5)."));
add(B("Dữ liệu theo dõi chỉ 22 ngày nên không đánh giá được biến động theo mùa trong năm."));
add(B(`Chỉ ${S.n_ch_H} kênh có video trong H và ${R.q1_between_share}% phương sai nằm giữa các kênh, nên so sánh theo giờ, thứ, thể loại lẫn với khác biệt giữa kênh; kiểm tra “trừ trung vị kênh” chỉ là bước kiểm tra độ vững, không phải mô hình đầy đủ (xem Q3).`));
add(B("like_rate chưa được chuẩn hóa theo tuổi video và chỉ tính cho video không ẩn lượt thích; ô giờ × thứ ở các giờ ít video (ví dụ 4 giờ sáng) có cỡ mẫu nhỏ."));

// ================================================================== 5.3b
add(H2("5.3b Q3b: Hồi quy Logistic"));
add(BEAT("Phương pháp."));
add(P(`Biến phụ thuộc là viral_A (1 nếu video nằm trong 10% cao nhất theo lượt xem của nhóm tuổi). Biến độc lập là X_PRE (Mục 4.5). Biến số được chuẩn hóa z-score nên odds ratio (OR) hiểu theo mỗi tăng 1 độ lệch chuẩn; biến nhị phân giữ 0/1 nên OR là “có so với không”. Do duration_sec và total_videos lệch phải rất mạnh, nhóm lấy log10(duration_sec) và log10(total_videos + 1) trước khi chuẩn hóa. category_id là biến nhóm với nhóm gốc là ${F.ref}; thể loại có dưới 100 video bị gộp, và vì nhóm gộp chỉ còn ${F.removed_cat} video nên các video đó bị loại để tránh ước lượng không ổn định (tách hoàn toàn) với một nhóm quá nhỏ. Hai mô hình: M1 đủ biến; M2 bỏ nhóm biến kênh (log_subs, channel_age_days, total_videos). Thêm M3 (độ vững) thay pub_hour bằng 5 khung giờ pub_slot. Python: statsmodels Logit với cov_type = “cluster” theo channel_id; R: glm(family = binomial) với sandwich::vcovCL(cluster = ~channel_id) và lmtest::coeftest. Sai số chuẩn bền vững theo kênh cần thiết vì các video cùng kênh có sai số tương quan, và khi bỏ qua điều đó sai số chuẩn mặc định có thể đánh giá độ chính xác quá cao (Cameron và Miller, 2015). Báo OR, khoảng tin cậy 95% (Wald), AIC, McFadden R² và VIF.`));
add(BEAT("Kết quả và mức ý nghĩa."));
add(P(`Cỡ mẫu: n = **${F.n}** video thuộc n_H = ${S.n_H} từ **${F.clusters}** kênh (cụm), trong đó **${F.n_pos}** video dương (${F.pct_pos}%) (${R.data_label}).`));
const q3rows = R.q3b_rows.map((r) => [r[0], r[1], r[3], r[5]]);
q3rows.push(["AIC", F.aic1, F.aic2, ""]);
q3rows.push(["McFadden R²", F.mf1, F.mf2, ""]);
add(table([2900, 2300, 2300, 1621], ["Biến", "OR – M1 (CI 95%)", "OR – M2 (CI 95%)", "VIF (M1)"], q3rows, { sz: 18, aligns: [AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER] }));
add(CAPT("Bảng 5.8. Kết quả hồi quy Logistic cho viral_A (nguồn: outputs/q3b/q3b_or_table.csv). Thể loại so với nhóm gốc Gaming; biến số: OR theo +1 độ lệch chuẩn"));
add(figure(FIG("q3b/q3b_forest_M1.png"), 7000, 7600));
add(CAPF("Hình 5.3b. Odds ratio của M1 (thang log) và khoảng tin cậy 95% bền vững theo kênh (nguồn: outputs/q3b/q3b_forest_M1.png)"));
add(P(`**Nhóm biến kênh chi phối.** Trong M1, mỗi tăng 1 độ lệch chuẩn của log_subs đi cùng odds gấp **${K.subs}** lần; tuổi kênh có OR ${K.age} và log số video của kênh có OR ${K.tv}, tức khi số người đăng ký như nhau, kênh lâu năm hoặc nhiều video hơn có odds thấp hơn. Bỏ ba biến kênh (M2) làm McFadden R² giảm từ ${F.mf1} xuống ${F.mf2} và AIC tăng ${F.daic} (${F.aic1} lên ${F.aic2}); thống kê tỷ số hợp lý giữa hai mô hình là ${F.lr} (chỉ tham khảo, chưa hiệu chỉnh cụm). Mô hình thay khung giờ M3 cho kết quả gần như giống M1 (AIC ${F.aic3}; OR của log_subs ${K.m3_subs}).`));
add(P(`**Thể loại.** So với Gaming, ${R.q3b_dyn.n_cat_below1}/${R.q3b_dyn.n_cat} thể loại có odds thấp hơn theo điểm ước lượng, nhưng chỉ ${R.q3b_dyn.n_cat_ci_below1} thể loại có khoảng tin cậy 95% hoàn toàn dưới 1 (${R.q3b_dyn.cat_ci_below1.join(", ")}); ${R.q3b_dyn.n_cat_ci_has1} thể loại còn lại có khoảng tin cậy chứa 1 (${R.q3b_dyn.cat_ci_has1.join(", ")}), tức chưa phân biệt được với Gaming. Điều này không mâu thuẫn với Mục 5.1: chênh lệch thô theo thể loại ở đó phần lớn phản ánh cơ cấu kênh, và sau khi trừ trung vị kênh, khác biệt giữa các thể loại chỉ còn rất nhỏ.`));
add(P(`**Thời gian, độ dài và tiêu đề.** Khi đã kiểm soát kênh và thể loại, giờ đăng (OR ${K.hour}) và cuối tuần (OR ${K.weekend}) không có liên quan rõ rệt; độ dài video, video ngắn, số tag và ${R.q3b_dyn.n_title_ci_has1_m1}/${R.q3b_dyn.n_title} đặc điểm tiêu đề đều có khoảng tin cậy chứa 1. Trong ${R.q3b_nsig.n_terms} hệ số của M1, có ${R.q3b_nsig.n_sig} hệ số có p < 0,05; chỉ ${R.q3b_nsig.n_sig_nonchan_noncat} hệ số trong số đó không thuộc nhóm kênh hay thể loại: ${R.q3b_dyn.nonchan_sig.join("; ")}. Với ${R.q3b_nsig.n_terms} hệ số được xét đồng thời, một vài p gần 0,05 có thể chỉ là ngẫu nhiên; riêng pub_month được mã hóa tuyến tính từ 1 đến 12 trong khi dữ liệu trải trên ba năm nên nhóm không diễn giải hệ số này.`));
const D3 = R.q3b_dyn;
add(P(`**Khi bỏ nhóm biến kênh (M2),** ${D3.m2_title_sig.length ? `một số dấu hiệu tiêu đề trở nên có ý nghĩa thống kê (${D3.m2_title_sig.join("; ")})` : "không dấu hiệu tiêu đề nào đạt ý nghĩa thống kê"}${D3.m2_title_near.length ? `, và một số khác tiến sát ngưỡng 0,05 (${D3.m2_title_near.join("; ")})` : ""}; đồng thời các hệ số thể loại đổi mạnh (ví dụ News & Politics từ OR ${D3.news[0]} ở M1 xuống ${D3.news[1]} ở M2). Điều này gợi ý các đặc điểm tiêu đề và thể loại đang đại diện cho phong cách hoặc quy mô kênh khi biến kênh bị bỏ, chứ không phải tác động độc lập.`));
add(P(`**Đa cộng tuyến.** Mọi biến có VIF ≤ ${K.vif_max_other} trừ title_len (VIF ${K.vif_len}) và title_words (VIF ${K.vif_words}); hai biến này vượt ngưỡng 5 nhưng chưa vượt 10 nên được giữ, tuy nhiên khoảng tin cậy của chúng rộng và không nên diễn giải riêng lẻ.`));
add(BEAT("Giải thích thực tiễn."));
add(P(`Kết quả cho thấy khả năng một video nằm trong top 10% của nhóm tuổi có liên quan mạnh nhất đến quy mô và đặc điểm của kênh đăng; thể loại cũng có liên quan rõ rệt, còn những yếu tố mà người đăng chủ động điều chỉnh sau khi đã chọn kênh và thể loại (giờ đăng, độ dài, tag, cách đặt tiêu đề) có liên quan yếu hoặc không phân biệt được với 0. Điều này nhất quán với Mục 5.1, nơi khác biệt giữa kênh lớn hơn nhiều so với khác biệt theo giờ. Cần đọc OR là tỷ số odds chứ không phải tỷ số xác suất: vì tỷ lệ dương chỉ khoảng 10%, odds gần bằng xác suất khi xác suất nhỏ, nhưng OR khoảng ${K.subs.split(" ")[0]} không có nghĩa xác suất tăng gấp ${K.subs.split(" ")[0]} lần. Sai số chuẩn bền vững theo kênh làm khoảng tin cậy rộng hơn so với sai số mặc định, nên các kết luận ở trên đã tính đến việc các video cùng kênh không độc lập (Cameron và Miller, 2015).`));
add(BEAT("Khuyến nghị."));
add(B("Nhãn hàng và MCN khi chọn kênh hợp tác để mong video “nổi bật so với cùng tuổi” nên xem quy mô và hồ sơ kênh là dấu hiệu có liên quan mạnh nhất; không nên kỳ vọng mẹo về giờ đăng hay tiêu đề bù được khoảng cách này."));
add(B("Nhà sáng tạo ở kênh nhỏ nên tập trung vào lựa chọn thể loại và nội dung phù hợp với đối tượng của mình hơn là các mẹo định dạng tiêu đề; bằng chứng của đồ án không cho thấy giờ đăng, độ dài video hay phần lớn các đặc điểm tiêu đề có liên quan rõ rệt với việc nổi bật khi đã kiểm soát kênh; riêng dấu ngoặc trong tiêu đề có liên hệ dương nhẹ nhưng cần kiểm chứng thêm vì đã xét nhiều hệ số cùng lúc."));
add(B("Khi báo cáo hiệu quả theo thể loại cho khách hàng, nên nêu nhóm gốc và nhắc rằng thể loại không tách rời kênh (hệ số thể loại đổi mạnh khi bỏ biến kênh)."));
add(BEAT("Hạn chế."));
add(B("Nhãn viral_A là nhãn tương đối theo nhóm tuổi, không phải “viral” theo nghĩa lọt Trending."));
add(B("Odds ratio mô tả liên hệ, không phải quan hệ nhân quả; đặc biệt, số người đăng ký đo lúc thu thập (sau khi video đã đăng) và được làm tròn xuống ba chữ số có nghĩa (Google for Developers, n.d.), nên có thể một phần là hệ quả của video nổi bật chứ không chỉ là nguyên nhân."));
add(B(`Chỉ ${F.clusters} kênh tạo nên toàn bộ mẫu; một số ít kênh lớn có thể chi phối hệ số, và kết quả không đại diện cho toàn bộ YouTube Việt Nam.`));
add(B("pub_hour, pub_dow, pub_month được đưa vào dạng số tuyến tính theo X_PRE; M3 chỉ kiểm tra riêng giờ đăng. duration_sec và total_videos được lấy log10 (khác danh sách thô ở Bảng 4.2); title_len và title_words gần đa cộng tuyến."));
add(B("McFadden R² chỉ so sánh được giữa các mô hình trên cùng dữ liệu, không đọc như R² của hồi quy tuyến tính; chưa đánh giá khả năng dự báo ngoài mẫu (thuộc Mục 5.5)."));

// ================================================================== Phụ lục C, D
add(new Paragraph({ children: [new PageBreak()] }));
add(H2("Phụ lục C: Bảng độ tin cậy và từ điển dữ liệu (phần của Bảo)"));
add(P("Bảng độ tin cậy đầy đủ là Bảng 3.3 ở Mục 3.3 (outputs/reliability/reliability_table.csv). Bảng C.1 trích các cột thường dùng của videos_master.csv; từ điển đầy đủ cho cả 55 cột của videos_master.csv và các file measurements.csv, trending_clean.csv, channels_latest.csv nằm trong docs/data_dictionary.md (sinh bằng gen_data_dictionary.py); dq_report.txt được mô tả ở cuối file này."));
add(table([1500, 2300, 1000, 2700, 1621], ["Cột", "Ý nghĩa", "Đơn vị", "Cách tính", "Có thể rỗng? Vì sao"], R.dict_rows.map((r) => [r[0], r[1], r[2], r[3], r[4]]), { sz: 17, aligns: Array(5).fill(AlignmentType.LEFT) }));
add(CAPT("Bảng C.1. Trích từ điển dữ liệu (nguồn: docs/data_dictionary.md)"));
add(H2("Phụ lục D: Dashboard Power BI (phần của Bảo)"));
const D_IMGS = ["Hinh_D1.png", "Hinh_D2.png", "Hinh_D3.png", "Hinh_D4.png"].map((f) => path.join(__dirname, "assets", f));
if (D_IMGS.every((f) => fs.existsSync(f))) {
  add(P("Bốn trang dashboard được dựng từ các CSV trong outputs/powerbi/ và lưu trong dashboard.pbix. Ảnh chụp giữ nguyên bố cục; số trên dashboard đã đối chiếu với Bảng 3.3, Bảng 5.1 và Bảng 5.8."));
  add(figure(D_IMGS[0], 8200, 6200));
  add(CAPF("Hình D.1. Trang 1 - Tổng quan: cỡ mẫu, độ tin cậy và Q1 (nguồn: dashboard.pbix, outputs/powerbi/)"));
  add(new Paragraph({ children: [new PageBreak()] }));
  add(figure(D_IMGS[1], 8200, 6200));
  add(CAPF("Hình D.2. Trang 2 - Giờ đăng và thể loại: nhịp giờ, heatmap giờ × thứ, thể loại và Q2b (nguồn: dashboard.pbix, outputs/powerbi/)"));
  add(new Paragraph({ children: [new PageBreak()] }));
  add(figure(D_IMGS[2], 8200, 6200));
  add(CAPF("Hình D.3. Trang 3 - Viral: Q3b Logistic (odds ratio, so sánh M1/M2/M3) và Q5 (so sánh mô hình, importance, bỏ nhóm biến kênh) (nguồn: dashboard.pbix, outputs/powerbi/)"));
  add(new Paragraph({ children: [new PageBreak()] }));
  add(figure(D_IMGS[3], 8200, 6200));
  add(CAPF("Hình D.4. Trang 4 - Cụm và dự báo: Q6 K-means (PCA, hồ sơ cụm) và Q4 dự báo S1/S2 (nguồn: dashboard.pbix, outputs/powerbi/)"));
} else {
  add(P("Bản nộp này chưa kèm 4 ảnh dashboard Power BI vì chưa hoàn tất thao tác trong Power BI Desktop. Các CSV đầu vào cho bốn trang đã được chuẩn bị trong outputs/powerbi/; hướng dẫn dựng trang, công thức DAX và cách xuất ảnh nằm trong docs/PowerBI_guide.md. Khi có ảnh, đặt tên Hinh_D1.png đến Hinh_D4.png trong report/assets/ rồi chạy lại build_muc_bao.js; phụ lục này sẽ tự chèn ảnh."));
}

// ------------------------------------------------------------------ tài liệu tham khảo của phần này
add(H2("Tài liệu tham khảo của phần này"));
const refPara = (parts) => new Paragraph({ spacing: { line: 276, after: 80 }, indent: { left: 432, hanging: 432 }, alignment: AlignmentType.LEFT,
  children: parts.map(([t, i]) => new TextRun({ text: t, italics: !!i })) });
add(refPara([["Cameron, A. C., & Miller, D. L. (2015). A practitioner’s guide to cluster-robust inference. "], ["Journal of Human Resources, 50", true], ["(2), 317–372. https://doi.org/10.3368/jhr.50.2.317"]]));
add(refPara([["DataReportal. (2026). "], ["Digital 2026: Vietnam", true], [". https://datareportal.com/reports/digital-2026-vietnam"]]));
add(refPara([["Google for Developers. (n.d.). "], ["Channels", true], [" [YouTube Data API reference]. Google. Retrieved November 10, 2026, from https://developers.google.com/youtube/v3/docs/channels"]]));
add(refPara([["Tuoi Tre News. (2026, September 17). "], ["Vietnam has more than 180,000 YouTube channels with over 10,000 subscribers", true], [". https://news.tuoitre.vn/vietnam-has-more-than-180000-youtube-channels-with-over-10000-subscribers-103260917213741415.htm"]]));
add(refPara([["YouTube Help. (n.d.). "], ["How engagement metrics are counted", true], [". Google. Retrieved November 10, 2026, from https://support.google.com/youtubecreatorstudio/answer/2991785"]]));

// ------------------------------------------------------------------ tài liệu
const doc = new Document({
  creator: "Nguyễn Gia Bảo", title: "Muc_Bao", description: "Mục 3.1–3.5, 5.1, 5.3b, Phụ lục C, D",
  styles: {
    default: { document: { run: { font: FONT, size: 26 }, paragraph: { spacing: { line: 360 }, alignment: AlignmentType.JUSTIFIED } } },
    paragraphStyles: [
      { id: "Heading1", name: "heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 32, bold: true }, paragraph: { spacing: { before: 240, after: 120, line: 360 }, alignment: AlignmentType.LEFT, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 28, bold: true }, paragraph: { spacing: { before: 240, after: 120, line: 276 }, alignment: AlignmentType.LEFT, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 26, bold: true }, paragraph: { spacing: { before: 200, after: 100, line: 276 }, alignment: AlignmentType.LEFT, keepNext: true, outlineLevel: 2 } },
      { id: "CaptionTable", name: "Caption Bang", basedOn: "Normal", run: { font: FONT, size: 22, italics: true }, paragraph: { alignment: AlignmentType.CENTER, spacing: { line: 276 } } },
      { id: "CaptionFigure", name: "Caption Hinh", basedOn: "Normal", run: { font: FONT, size: 22, italics: true }, paragraph: { alignment: AlignmentType.CENTER, spacing: { line: 276 } } },
    ],
  },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1418, bottom: 1418, left: 1985, right: 1134, header: 720, footer: 720 } } },
    children: kids,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log("Đã ghi", OUT, Math.round(b.length / 1024) + " KB"); });
