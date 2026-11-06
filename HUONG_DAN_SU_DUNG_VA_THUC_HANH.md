# Hướng dẫn sử dụng và thực hành làm chủ TikTok Trend Hunter

> Hướng dẫn này dành cho phiên bản chạy cục bộ trên Windows, giao diện tiếng Việt. Ứng dụng hỗ trợ sàng lọc sản phẩm TikTok Shop VN bằng dữ liệu quan sát được; đây là công cụ hỗ trợ quyết định, không phải cam kết doanh số hay lợi nhuận.

## 1. Bắt đầu trong 2 phút

1. Mở thư mục dự án và chạy `start.bat`. Ứng dụng kiểm tra backend/frontend rồi mở Dashboard tại <http://127.0.0.1:3000>.
2. Nếu ứng dụng đã chạy, mở địa chỉ trên thay vì chạy thêm một bản khác.
3. Trên Dashboard, nhìn trạng thái Crawler và thời điểm quét gần nhất. Bấm biểu tượng làm mới nếu muốn tải lại dữ liệu hiện tại.
4. Mở tab **Trending** để xem sản phẩm có đủ dữ liệu xu hướng; xem **Rising** để tìm sản phẩm có tốc độ bán dương; xem **Mới Phát Hiện** và **Bán Chạy Nhất** để có thêm góc nhìn.
5. Mở một sản phẩm để kiểm tra lịch sử, tín hiệu và giả định kinh tế trước khi đưa vào danh sách làm việc.

Nếu giao diện báo không kết nối được backend, mở **Hệ thống** ở góc phải hoặc chạy `healthcheck.bat`. Khi cần khởi động lại dịch vụ, dùng `RESTART.bat` theo hướng dẫn trong `README.md`.

## 2. Quy trình săn sản phẩm hằng ngày

### Bước A — Thu thập dữ liệu có chủ đích

Trên vùng điều khiển Crawler:

- **Chạy Crawler Ngay** khởi chạy lượt quét theo cấu hình hiện tại.
- Mở **Quét theo Link / Từ khóa** để nhập một hoặc nhiều URL sản phẩm TikTok Shop, mỗi URL một dòng. Mỗi lần nhận tối đa 100 URL duy nhất.
- Từ khóa ngành hàng là tùy chọn. Crawler discovery diện rộng có thể bị TikTok trả về `Security Check`; vì vậy không xem tìm kiếm theo từ khóa là cách đảm bảo luôn tìm được sản phẩm mới.
- Không khởi chạy lượt quét thứ hai khi lượt trước còn chạy. Ứng dụng chặn lượt chạy đồng thời.

Theo dõi trạng thái kết thúc:

- `completed`: lượt quét hoàn tất.
- `partial`: một phần công việc hoàn tất. Sản phẩm đã theo dõi có thể vẫn được cập nhật dù discovery sản phẩm mới gặp lỗi.
- `failed`: lượt quét thất bại; đọc thông báo lỗi trên Dashboard và kiểm tra **Hệ thống**.

Khi gặp `Security Check`, có thể chủ động đăng nhập TikTok bằng `CONNECT_TIKTOK.bat`, xác minh trong cửa sổ được mở, rồi nhập `SAVE` ở terminal. Phiên chỉ lưu trên máy tại `backend/.local/tiktok-session.json`; không chia sẻ tệp này. Có phiên hợp lệ không đồng nghĩa TikTok chắc chắn cho phép truy cập Shop.

### Bước B — Sàng lọc danh sách

| Tab | Dùng để | Lưu ý |
|---|---|---|
| **Trending** | Xem sản phẩm đủ điều kiện xếp hạng xu hướng | Dùng bộ lọc trạng thái, bằng chứng và cách sắp xếp để giảm nhiễu |
| **Rising** | Tìm sản phẩm đang có tốc độ bán dương | Tập trung vào biến động gần đây, không chỉ tổng bán tích lũy |
| **Mới Phát Hiện** | Xem sản phẩm hệ thống lần đầu ghi nhận trong 24 giờ, 3 ngày hoặc 7 ngày | “Mới phát hiện” không có nghĩa là sản phẩm vừa được đăng bán |
| **Bán Chạy Nhất** | Xếp hạng theo tổng đã bán, lượng bán 24 giờ hoặc 7 ngày | Tổng bán cao không tự nó chứng minh sản phẩm đang tăng tốc |
| **Watchlist** | Theo dõi sản phẩm đã đánh dấu ngôi sao | Quét định kỳ giúp tạo thêm quan sát để xem biến động |
| **Bộ sưu tập** | Tổ chức sản phẩm thành các nhóm công việc | Có trạng thái đánh giá và ghi chú quyết định riêng cho từng sản phẩm |

Trên danh sách, có thể tìm theo tên/shop, lọc danh mục, đặt điểm xu hướng tối thiểu và đổi chiều sắp xếp. Với **Trending** và **Watchlist**, các bộ lọc chính gồm:

- **Trạng thái dữ liệu:** đủ điều kiện xu hướng; tất cả sản phẩm theo dõi; dữ liệu cũ hơn 8 giờ; hoặc chưa đủ tín hiệu qua hai chu kỳ đo.
- **Độ tin cậy & bằng chứng:** tất cả; tin cậy cao (ít nhất 5 quan sát, khoảng 24 giờ chuẩn); trung bình trở lên; hoặc chỉ số đo chuẩn khoảng 24 giờ, không dùng ước tính.
- **Sắp xếp:** điểm xu hướng, tốc độ bán 24 giờ, lượng bán 24 giờ thực tế, lượt đánh giá mới hoặc thời điểm cập nhật.

Mẹo: khi lập danh sách ứng viên nghiêm túc, thử `Chỉ đo lường chuẩn ~24h` và `Tin cậy Cao`. Nếu danh sách trống, đó thường là dấu hiệu chưa có đủ lịch sử; hãy theo dõi thêm thay vì nới lọc rồi coi ước tính là dữ liệu chắc chắn.

### Bước C — Thẩm định trang chi tiết

Mở thẻ sản phẩm để xem thông tin và phân tích. Dùng **Lịch sử sản phẩm** với khoảng 24h, 7d, 30d hoặc Tất cả để đối chiếu các snapshot. Bảng snapshot cho biết các giá trị đã ghi nhận như giá, lượng bán, lượt đánh giá, rating và hoa hồng nếu nguồn có cung cấp.

- Giá và các số liệu mô tả trạng thái lúc thu thập; giá có thể thay đổi theo ưu đãi, phân loại và phiên truy cập.
- Chỉ số `—` là chưa có dữ liệu, không phải số 0. Dữ liệu thiếu không được tự suy diễn.
- Delta/tốc độ cần các lần chụp cách nhau đủ lâu. Lần quét đầu không tạo ra lịch sử tăng trưởng.
- Kiểm tra thời điểm chụp và độ tươi dữ liệu trước khi kết luận.

## 3. Từ ứng viên đến quyết định

### Theo dõi và đặt cảnh báo

1. Bấm biểu tượng ngôi sao trên thẻ để thêm sản phẩm vào **Watchlist**; bấm lại để bỏ theo dõi.
2. Trên trang chi tiết, mở thiết lập cảnh báo để tạo quy tắc theo tốc độ bán, điểm xu hướng hoặc phần trăm biến động giá.
3. Chọn ngưỡng có ý nghĩa với quy trình của bạn. Với biến động giá, chọn tăng, giảm hoặc cả hai; có thể đặt thời gian cooldown.
4. Mở Trung tâm cảnh báo ở thanh trên cùng để xem sự kiện, đánh dấu đã đọc hoặc xuất CSV.

Cảnh báo chỉ phát hiện khi dữ liệu quan sát thỏa quy tắc. Nó không thay thế việc xác nhận sản phẩm còn hàng, điều kiện affiliate hay chất lượng nội dung.

### So sánh và quản lý bộ sưu tập

- Dùng nút so sánh trên thẻ để đưa tối đa 5 sản phẩm vào khay so sánh. Việc chọn chỉ tồn tại trong phiên giao diện hiện tại.
- Tạo bộ sưu tập cho một mục tiêu cụ thể, ví dụ “Thử nội dung tuần này” hoặc “Chờ thêm dữ liệu”. Thêm sản phẩm vào nhóm từ thẻ sản phẩm.
- Dùng các trạng thái **Mới**, **Đang xem xét**, **Ứng viên**, **Đã loại** và ghi lý do quyết định trong ghi chú.
- Khi đã loại sản phẩm, có thể gỡ nó khỏi bộ sưu tập; thao tác đó không xóa sản phẩm khỏi cơ sở dữ liệu.

### Ước tính kinh tế affiliate

Trong phần kinh tế trên trang chi tiết, tạo một kịch bản và nhập các giả định bạn biết: tỷ lệ hoa hồng, cơ sở tính hoa hồng, chi phí mẫu/nội dung/khuyến mại, chi phí biến đổi mỗi đơn và số đơn dự kiến. Có thể nhân bản kịch bản để so sánh nhiều phương án và đặt một kịch bản làm mặc định.

Đọc các kết quả như hoa hồng ước tính mỗi đơn, lợi nhuận đóng góp mỗi đơn và số đơn cần để hòa vốn. Đây là mô hình theo giả định bạn nhập; xác nhận lại tỷ lệ/cơ sở hoa hồng với nguồn affiliate thực tế. Tốc độ bán của thị trường không phải đơn hàng affiliate được phân bổ cho bạn, vì vậy không nhân tốc độ bán với hoa hồng để tự kết luận thu nhập.

### Video TikTok liên quan

Ở phần video của trang sản phẩm, dán URL video và bấm **Gắn video**. Liên kết là do bạn quản lý, không xác nhận video thực sự quảng bá sản phẩm. Có thể làm mới metadata hoặc gỡ liên kết.

Metadata lấy từ TikTok oEmbed. Các số lượt xem/thích/bình luận/chia sẻ chỉ hiện nếu có nguồn đo lường khả dụng; hiện chưa có nguồn public đã xác thực để bảo đảm thu thập các counters này. Không coi tương tác là doanh số hoặc hoa hồng.

## 4. Lưu góc nhìn, xuất dữ liệu và bảo vệ dữ liệu

- **Saved View:** trên Trending hoặc Watchlist, lưu cấu hình bộ lọc/sắp xếp thường dùng để áp dụng lại.
- **CSV:** dùng nút Xuất CSV ở Trending, Watchlist, Trung tâm cảnh báo hoặc lịch sử sản phẩm. Lịch sử chỉ xuất được các khoảng 24h, 7d, 30d; lựa chọn Tất cả chỉ để xem trên giao diện.
- **Sao lưu:** chạy `BACKUP.bat` từ thư mục gốc. Bản sao hợp lệ được lưu dưới `backend/.local/backups/`.
- **Phục hồi:** chỉ thực hiện khi cần và có đúng file backup tương thích. Dùng `RESTORE.bat <đường-dẫn-file-backup>`; launcher sẽ dừng dịch vụ, tạo safety backup, kiểm tra, thay cơ sở dữ liệu và xác nhận health. Đây là thao tác thay thế dữ liệu hiện hành, nên đọc kỹ tên file trước khi chạy.
- Mở **Hệ thống → Sao lưu & Phục hồi** để xem hướng dẫn tích hợp. Tab **Tổng quan & Toàn vẹn** hiển thị tình trạng database, crawler, scheduler và có kiểm tra toàn vẹn chuyên sâu.

## 5. Kế hoạch thực hành 7 ngày

### Ngày 1 — Làm quen và tạo baseline

- Mở các tab, chọn một danh mục, tìm sản phẩm.
- Quét một nhóm nhỏ URL sản phẩm hợp lệ.
- Chọn 3–5 sản phẩm có dữ liệu và thêm vào Watchlist.
- Ghi lại thời điểm snapshot đầu; chưa diễn giải tốc độ tăng trưởng.

### Ngày 2–3 — Tạo lịch sử

- Để crawler chạy theo lịch hiển thị và kiểm tra trạng thái từng lượt.
- Mở lại cùng sản phẩm, xem **Lịch sử sản phẩm** và quan sát liệu đã có ít nhất hai lần chụp hữu ích chưa.
- Tạo bộ sưu tập, chuyển sản phẩm qua trạng thái xem xét và ghi rõ điều kiện cần xác minh.

### Ngày 4–5 — Kiểm tra tín hiệu

- Dùng Rising và Trending; đối chiếu tốc độ, lượng bán 24 giờ, lượt đánh giá mới, độ tin cậy và độ mới của dữ liệu.
- So sánh tối đa 5 sản phẩm.
- Tạo kịch bản kinh tế thận trọng và một kịch bản lạc quan; ghi giả định thay vì xem kết quả là dự báo chắc chắn.
- Chỉ gắn video đã tự kiểm tra nội dung và sản phẩm.

### Ngày 6–7 — Chốt quy trình cá nhân

- Xem lại Watchlist, lịch sử và sự kiện cảnh báo; loại sản phẩm không còn phù hợp hoặc đánh dấu ứng viên.
- Xuất CSV cần thiết, tạo backup định kỳ.
- Viết ra bộ tiêu chí riêng: mức tăng tối thiểu, độ tin cậy, giới hạn chi phí và lý do loại sản phẩm.
- Đánh giá liệu dữ liệu và quy trình đã đủ hữu ích hay cần một khả năng mới. Phase 8 chưa mở; các tính năng mới cần một mục tiêu sản phẩm cụ thể.

## 6. Cách đọc tín hiệu mà không tự đánh lừa mình

1. **Tổng bán là quy mô tích lũy; Rising là động lượng gần đây.** Một sản phẩm bán nhiều lâu nay chưa chắc đang tăng nhanh hôm nay.
2. **Ít quan sát thì ít chắc chắn.** Chờ đủ chu kỳ quét; dùng bộ lọc bằng chứng để tách số đo chuẩn khỏi tốc độ ước tính.
3. **Dữ liệu cũ không đại diện cho hiện tại.** Kiểm tra dấu thời gian và trạng thái cũ hơn 8 giờ.
4. **Đừng biến thiếu dữ liệu thành số không.** `—` thường nghĩa là nguồn chưa cung cấp hoặc chưa đủ lịch sử.
5. **Điểm xu hướng là tín hiệu sàng lọc**, không phải xác suất thành công, dự báo lợi nhuận hay xác nhận affiliate.
6. **Discovery diện rộng có giới hạn hiện tại.** TikTok có thể trả Security Check; CAPTCHA bypass không thuộc phạm vi ứng dụng. URL sản phẩm cụ thể là luồng thu thập đáng tin cậy hơn khi bạn đã có nguồn link.

## 7. Sự cố thường gặp

| Triệu chứng | Việc nên làm |
|---|---|
| Dashboard không tải dữ liệu | Bấm Tải lại; chạy `healthcheck.bat`; kiểm tra backend và frontend có đang hoạt động |
| Crawler báo `Security Check` | Thử luồng đăng nhập chủ động bằng `CONNECT_TIKTOK.bat`; quét lại URL sản phẩm; lưu ý phiên đăng nhập không bảo đảm quyền truy cập |
| Lượt quét `partial` | Đọc thông báo; kiểm tra sản phẩm đã theo dõi có được cập nhật không; discovery có thể bị chặn riêng |
| Trending trống | Kiểm tra đã có ít nhất hai snapshot chưa; xem filter trạng thái/bằng chứng; tiếp tục thu thập thay vì xem dữ liệu thiếu như xu hướng bằng 0 |
| Biểu đồ lịch sử trống | Chọn khoảng rộng hơn hoặc chờ thêm snapshot; biểu đồ chỉ dùng những lần thu thập đã lưu |
| Video không có metrics | Đây là trạng thái có thể xảy ra; metadata video không đồng nghĩa đã có số liệu tương tác |
| Cần chuyển máy/khôi phục | Tạo backup trước; chỉ phục hồi từ backup tương thích bằng `RESTORE.bat`; phiên TikTok cục bộ không nằm trong backup |

## 8. Quy trình sử dụng mẫu (checklist 10 phút)

- [ ] Dashboard và Crawler đang kết nối bình thường.
- [ ] Kiểm tra lần quét gần nhất và trạng thái `completed`/`partial`/`failed`.
- [ ] Lọc Trending theo độ tin cậy phù hợp, xem Rising và sản phẩm mới.
- [ ] Mở tối đa vài ứng viên; kiểm tra snapshot, giá, delta và thời điểm đo.
- [ ] Thêm ứng viên vào Watchlist hoặc bộ sưu tập, ghi lý do.
- [ ] Đối chiếu điều kiện affiliate và nhập giả định thực tế vào kịch bản kinh tế.
- [ ] Đặt cảnh báo chỉ cho ngưỡng có ích.
- [ ] Cuối tuần xuất CSV và tạo backup.

## 9. Tài liệu tham khảo trong dự án

- [README.md](README.md) — khởi chạy, phiên TikTok, CSV và backup/restore.
- [PROJECT_STATUS.md](PROJECT_STATUS.md) — phạm vi hỗ trợ, trạng thái hiện tại và các giới hạn đã biết.
- [PROJECT_CONTROL_PHASE8_SELECTION.md](PROJECT_CONTROL_PHASE8_SELECTION.md) — vì sao Phase 8 chưa được mở.
- [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) — quy trình vận hành và restart dịch vụ.
