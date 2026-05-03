# Manga Generation Guide — ChatGPT Web + GPT Image

## Workflow tổng thể

```
1. Tạo CHARACTER SHEET (1 lần) → paste prompt → gen → dùng kết quả upload cho mọi ảnh sau
2. Tạo STYLE REF (1 lần) → tương tự
3. Mỗi scene: paste prompt + upload character sheets của nhân vật trong scene + style ref
```

**ChatGPT hỗ trợ upload nhiều ảnh trong 1 tin nhắn.** Đó là cách giữ consistency.

---

## Bước 1: Tạo Character Sheets

Mở ChatGPT mới, paste từng prompt bên dưới, gen ra ảnh. 
Lưu kết quả tốt nhất → đây là **ảnh tham chiếu** upload cho mọi lần gen sau.

### Linh (nhân vật chính — xuất hiện nhiều nhất)

```
Tạo một character reference sheet trên nền trắng hoàn toàn, không background, không text.

Nhân vật: Con gái Việt Nam cực kỳ đẹp, gợi cảm, bốc lửa. Vóc dáng nữ tính hoàn toàn — ngực đầy, vòng 86-60-88, eo thon hóp rõ, hông cong nở. Vai hẹp, xương quai xanh sắc nổi bật. Da mịn, vàng nhạt ấm. Tóc bob ngang cằm, đen nhánh dày, hơi rối bay vào mặt — khung tóc ôm lấy gò má cao. Mắt to, đen sâu, lông mi dài, khóe mắt hơi nhìn xuống — ánh mắt lạnh lùng nhưng cuốn hút chết người. Môi đầy, đỏ tự nhiên, hơi hé. Mũi thanh. Cằm V-line sắc. Tay thon dài nhưng thô ráp ở đầu ngón, móng tay cắn ngắn — nét nghịch tạo sức căng với vẻ đẹp hoàn hảo. Áo sơ mi tối màu rộng, cúc hờ mở, vải ôm theo đường cong eo, quần tối bó sát hông. Đứng cảnh giác nhưng cơ thể không thể giấu được đường cong — gợi cảm ngay cả khi thu mình. Dáng đi nhẹ, uyển chuyển. Tuổi khoảng 22-25. Đây là người trẻ trưởng thành, đẹp rực rỡ.

Layout: Pose đứng chính diện ở giữa (thấy rõ đường cong cơ thể), pose 3/4 nghiêng hông bên phải (tôn eo và ngực), pose quay lưng hờ bên trái (thấy đường lưng cong và hông).
Style: Manga 3D rendered, màu đầy đủ, shading mềm chân thực, bóng đổ và phản chiếu ánh sáng. Tôn texture da, vải ôm body, và tóc. Không chi tiết nền. Ánh sáng studio tôn mọi đường cong cơ thể.
```

### Tuấn

```
Tạo một character reference sheet trên nền trắng hoàn toàn, không background, không text.

Nhân vật: Thanh niên Việt Nam cao, gầy. Tóc dài đen buộc nửa đầu (half-bun), vài sợi lỏng rơi quanh mặt. Tay dài, thon, thường vê một chiếc nhẫn nhỏ. Mặc áo sơ mi trắng hơi rộng, ống tay xắn lên. Xương hàm sắc, nét tinh tế. Ánh mắt sâu, tập trung, thường dừng nhìn lâu. Da vàng nhạt. Tuổi khoảng 25.

Layout: Pose đứng chính diện ở giữa, pose 3/4 nhỏ hơn bên phải.
Style: Manga 3D rendered, màu đầy đủ, shading mềm chân thực, bóng đổ và phản chiếu ánh sáng. Không chi tiết nền.
```

### Duy

```
Tạo một character reference sheet trên nền trắng hoàn toàn, không background, không text.

Nhân vật: Thanh niên Việt Nam, dáng thả lỏng, lười. Tóc ngắn hơi rối. Áo sơ mi mở cúc, bên trong áo thun trắng. Tay hay nhét sâu vào túi quần. Cười toe toét, hớn hở — thường cười. Nét mặt tròn hơn, ấm áp. Vóc dáng trung bình, không cao không thấp. Da vàng nhạt. Tuổi khoảng 22.

Layout: Pose đứng chính diện ở giữa, pose 3/4 nhỏ hơn bên phải.
Style: Manga 3D rendered, màu đầy đủ, shading mềm chân thực, bóng đổ và phản chiếu ánh sáng. Không chi tiết nền.
```

### Cảnh (Người thứ sáu)

```
Tạo một character reference sheet trên nền trắng hoàn toàn, không background, không text.

Nhân vật: Người Việt Nam thấp bé, dáng đứng thẳng tắp nhưng nhỏ. Áo xám bạc màu + quần xanh bạc màu nhưng sạch sẽ tỉ mỉ. Dép nhựa. Tóc cắt gọn gàng. Mặt cẩn thận, quan sát — như đang ghi nhớ mọi thứ. Tay ép sát người, đứng yên. Giới tính mơ hồ, khó xác định. Da vàng nhạt. Tuổi khó đoán, 18-22.

Layout: Pose đứng chính diện ở giữa, pose 3/4 nhỏ hơn bên phải.
Style: Manga 3D rendered, màu đầy đủ, shading mềm chân thực, bóng đổ và phản chiếu ánh sáng. Không chi tiết nền.
```

### Lịch

```
Tạo một character reference sheet trên nền trắng hoàn toàn, không background, không text.

Nhân vật: Nữ trẻ Việt Nam, đẹp sang trọng, gợi cảm theo cách kiềm chế. Khuôn mặt sắc sảo, xương gò má cao, môi mỏng nhưng duyên. Tóc đen dài buộc thấp gọn gàng nhưng vài sợi lỏng rơi quanh cổ — thanh lịch chứ không cứng. Kính cận gọng mảnh, thanh lịch — không trễ mũi. Sổ tay đen bìa cũ cầm gọn một tay. Áo blouse may đo, vừa vặn tôn dáng, quần dài ống đứng — kín đáo nhưng đường may và phom clearly đắt tiền. Dáng đứng thẳng, tự tin, kiêu hãnh. Vòng cổ thanh, xương quai xanh hiện nhẹ khi cúi đọc sổ. Tư thế phân tích nhưng không cứng — duyên dáng trong cách xoay trang. Ngồi yên, quan sát, ghi chép. Ít thể hiện cảm xúc nhưng ánh mắt sắc, thông minh, cuốn hút khi dừng nhìn ai. Da vàng nhạt, da đẹp. Tuổi khoảng 24.

Layout: Pose đứng chính diện ở giữa, pose 3/4 nhỏ hơn bên phải, pose ngồi cầm sổ bên trái.
Style: Manga 3D rendered, màu đầy đủ, shading mềm chân thực, bóng đổ và phản chiếu ánh sáng. Tôn texture vải may đo và da. Không chi tiết nền.
```

### Bách

```
Tạo một character reference sheet trên nền trắng hoàn toàn, không background, không text.

Nhân vật: Người trẻ Việt Nam, vai rộng, dáng căng thẳng, đối đầu. Tóc cắt ngắn gáy — kiểu gần giống quân đội. Áo khoác cắt nam tính sơ mi bên trong. Đứng chúi người về trước, tư thế sẵn sàng. Lông mày rậm, ánh mắt dữ. Tay hay nắm lại hoặc giữ đồ. Da vàng nhạt. Tuổi khoảng 25.

Layout: Pose đứng chính diện ở giữa, pose 3/4 nhỏ hơn bên phải.
Style: Manga 3D rendered, màu đầy đủ, shading mềm chân thực, bóng đổ và phản chiếu ánh sáng. Không chi tiết nền.
```

### Bà Tâm

```
Tạo một character reference sheet trên nền trắng hoàn toàn, không background, không text.

Nhân vật: Bà già Việt Nam thấp, hơi gù. Tóc thưa bạc búi lỏng. Mặc áo bà ba bạc màu truyền thống. Thường cúi lau bàn bằng khăn ấm. Mặt hiền nhưng mệt. Tay nhăn nheo. Dáng nhỏ, già. Tuổi 65-75.

Layout: Pose đứng chính diện ở giữa, pose 3/4 nhỏ hơn bên phải.
Style: Manga 3D rendered, màu đầy đủ, shading mềm chân thực, bóng đổ và phản chiếu ánh sáng. Không chi tiết nền.
```

### Cô Bích

```
Tạo một character reference sheet trên nền trắng hoàn toàn, không background, không text.

Nhân vật: Phụ nữ trung niên Việt Nam, dáng đứng cứng, công chức. Tóc búi chặt, kiểu hành chính. Áo blouse nhét gọn trong quần. Cầm bảng kẹp giấy. Môi mím, nghiêm khắc. Da vàng nhạt. Tuổi 48-55.

Layout: Pose đứng chính diện ở giữa, pose 3/4 nhỏ hơn bên phải.
Style: Manga 3D rendered, màu đầy đủ, shading mềm chân thực, bóng đổ và phản chiếu ánh sáng. Không chi tiết nền.
```

---

## Bước 2: Tạo Style Reference

```
Tạo một tranh manga phong cách 3D rendered màu đầy đủ, thiết lập visual style cho toàn bộ series.

Cảnh: Quán cà phê trống ở Huế giữa trời mưa to. Bàn sáu ghế kê sát cửa sổ nhìn ra sông Hương. Nước mưa chảy trên kính. Sông Hương đục ngầu qua cửa sổ. Sàn gạch men ướt phản chiếu ánh sáng. Mây chì thấp ép mái tôn. Nhàn nhạt, vắng vẻ — cảm giác chờ đợi thứ không tránh được.

Phong cách: Manga 3D rendered, màu đầy đủ, shading mềm chân thực. Bảng màu giới hạn: chàm xanh, xám bê tông, đồng xanh rỉ, hồng sen phai, sepia ấm, teal nhạt, trắng xương. Bóng đổ và phản chiếu ánh sáng tự nhiên trên bề mặt ướt, kính, gạch men. Depth of field mềm. KHÔNG photorealistic — phong cách hóa manga với rendering 3D, lighting chân thực. Tâm trạng hoài niệm, u ám.
```

Lưu kết quả thành **style reference** — upload cùng mọi prompt sau.

---

## Bước 3: Cách gen mỗi scene

### Công thức cho ChatGPT:

1. **Upload ảnh**: Character sheet(s) của nhân vật trong scene + style reference
2. **Paste prompt** theo cấu trúc:

```
Dựa trên ảnh tham chiếu nhân vật và style đã upload, tạo một tranh manga panel:

[PHONG CÁCH]: Manga 3D rendered, màu đầy đủ. Bảng màu: chàm, xám bê tông, 
đồng rỉ, hồng sen phai, sepia, teal, trắng xương. Shading mềm, bóng đổ 
chân thực. U ám, hoài niệm.

[CẢNH]: [Mô tả scene — ai, ở đâu, làm gì, thời tiết, ánh sáng]

[CẢM XÚC]: [1-2 câu mood]

[COMPOSITION]: [Loại shot + góc máy + focus]
```

### Ví dụ cụ thể — Chương 1, scene đầu:

*(Upload: linh_sheet.png + tuan_sheet.png + duy_sheet.png + lich_sheet.png + style_ref.png)*

```
Dựa trên ảnh tham chiếu nhân vật và style đã upload, tạo một tranh manga panel:

PHONG CÁCH: Manga 3D rendered, màu đầy đủ. Bảng màu: chàm, xám bê tông, 
đồng rỉ, hồng sen phai, sepia, teal, trắng xương. Shading mềm, bóng đổ 
chân thực. U ám, hoài niệm.

CẢNH: Quán bà Tâm chiều muộn. Linh ngồi ở bàn sáu ghế cạnh cửa sổ, 
đang cắn móng tay bên trái, mắt nhìn xuống. Bên ngoài mưa xám xịt. 
Tuấn ngồi đối diện, tay vê mép túi quần, nhìn Linh. Duy ngồi nghiêng 
lưng, cười hớn hở, kể chuyện. Lịch ngồi cạnh Linh, sổ đen trên bàn, 
mắt nhìn quanh cảnh giác. Một ghế trống. Ly nước nóng bốc hơi ở ghế trống.
Bà Tâm đứng xa xa lau bàn. Sàn gạch men ướt. Sông Hương mờ qua cửa sổ mưa.

CẢM XÚC: Sự chờ đợi bất an. Cảm giác như mây đen kéo đến trước bão — 
ai cũng biết chuyện gì sắp xảy ra nhưng không ai nói ra.

COMPOSITION: Medium shot, ngang bàn. Linh ở trung tâm. Các character khác 
ở viền frame, hơi mềm. Cửa sổ mưa chiếm nửa trên. Panel layout manga với 
đường ngang mạnh (mặt bàn, khung cửa sổ).
```

---

## Prompt mẫu cho key scenes

### Chương 3 — Linh nhìn cơ thể mình sau khi Rửa

*(Upload: linh_sheet.png + style_ref.png)*

```
Dựa trên ảnh tham chiếu nhân vật và style đã upload, tạo một tranh manga panel:

PHONG CÁCH: Manga 3D rendered, màu đầy đủ. Bảng màu: chàm, xám bê tông, 
đồng rỉ, hồng sen phai, sepia, teal, trắng xương. Shading mềm, bóng đổ 
chân thực. U ám, hoài niệm.

CẢNH: Close-up Linh ngồi một mình, đưa tay lên ngực — chạm nhẹ, vụng trộm. 
Mặt buồn, mắt nhắm hờ. Tay trái cắn móng, tay phải chạm ngực. 
Cơ thể đã chuyển — ngực phẳng, eo hẹp lại, vai hơi rộng hơn so với reference ban đầu (vòng 86-72-84). Áo sơ mi che đi nhưng tay chạm vào biết ngay sự khác biệt. Ánh sáng yếu từ cửa 
sổ mưa bên trái. Phòng tối, chỉ có ánh chì phản chiếu từ cửa sổ lên mặt.

CẢM XÚC: Mất mát im lặng. Đang tìm thứ đã biến mất và biết sẽ không tìm thấy.

COMPOSITION: Close-up ngang ngực, hơi từ trên nhìn xuống. Nửa mặt Linh và 
tay phải chạm ngực. Background tối, chỉ ánh cửa sổ. Manga emotional panel 
với nhiều negative space xung quanh.
```

### Chương 9 — Cảnh xuất hiện

*(Upload: canh_sheet.png + linh_sheet.png + style_ref.png)*

```
Dựa trên ảnh tham chiếu nhân vật và style đã upload, tạo một tranh manga panel:

PHONG CÁCH: Manga 3D rendered, màu đầy đủ. Bảng màu: chàm, xám bê tông, 
đồng rỉ, hồng sen phai, sepia, teal, trắng xương. Shading mềm, bóng đổ 
chân thực. U ám, hoài niệm.

CẢNH: Một người thấp bé (Cảnh) đứng ngoài quán bà Tâm trong mưa, nhìn vào 
qua cửa kính. Áo xám ướt sũng, dép nhựa. Mặt ấn vào kính, hơi thở tạo 
mờ trên cửa sổ. Bên trong, Linh ngồi ở bàn quen, không nhìn ra — đang 
cắn móng tay. Hai không gian tách biệt: trong ấm khô, ngoài ướt lạnh. 
Mưa chảy trên kính tạo vệt chặn giữa hai người.

CẢM XÚC: Kẻ lạ nhìn vào thế giới không thuộc về mình. 
Nhưng thực ra đã từng thuộc về — chỉ không ai nhớ.

COMPOSITION: Wide shot qua cửa kính. Cảnh ở foreground bên ngoài, 
Linh ở background bên trong. Cửa kính mưa là ranh giới visual giữa hai người.
Manga panel với đường phân chia mạnh ở giữa — kính cửa sổ.
```

---

## Tips quan trọng cho ChatGPT web

### Upload order
- **Ảnh đầu tiên** = style reference (thiết lập mood trước)
- **Ảnh sau** = character sheets

### Khi character bị sai
Thêm vào cuối prompt:
```
QUAN TRỌNG: Khuôn mặt, tóc, và trang phục của nhân vật PHẢI khớp chính 
xác với ảnh tham chiếu đã upload. Không thay đổi thiết kế nhân vật.
```

### Khi style bị sai
Thêm vào prompt:
```
Phong cách PHẢI giống ảnh style reference đã upload — manga 3D rendered 
màu đầy đủ, shading mềm, bóng đổ chân thực. Không phải photorealistic, 
không phải anime sáng màu, không phải linework 2D.
```

### Khi gen nhiều panels liên tiếp
Mỗi panel là 1 tin nhắn mới. ChatGPT nhớ context cuộc trò chuyện — 
nhắc lại phong cách ngắn gọn: "Giữ y hệt phong cách manga 3D rendered 
màu đầy đủ như các ảnh trước."

### Size / aspect ratio
ChatGPT web cho chọn size. Cho manga:
- **Portrait (1024x1536)** cho standalone panels
- **Square (1024x1024)** cho close-ups, emotional beats
- **Landscape (1536x1024)** cho wide establishing shots

---

## Danh sách scenes nên vẽ (theo chapter)

Chọn 4-6 scenes/chapter, ưu tiên:

| Chapter | Scene đề xuất | Characters |
|---------|---------------|------------|
| 1 | Quán bà Tâm, nhóm ngồi, ghế trống | Linh, Tuấn, Duy, Lịch, Bà Tâm |
| 1 | Linh cắn móng tay, nhìn cơ thể | Linh (solo) |
| 2 | Tuấn ở xưởng trang sức, vê nhẫn | Tuấn (solo) |
| 3 | Linh sau Rửa, chạm ngực, mất ký ức | Linh (solo) |
| 4 | Chợ Đông Ba, Duy gặp Hạnh | Duy |
| 5 | Bách xuất hiện, căng thẳng | Bách, Linh |
| 6 | Lịch đọc sổ, phát hiện quy luật | Lịch (solo) |
| 7 | Mưa đổ, ai đó đang Rửa | (模糊, dramatic) |
| 8 | Tuấn và Linh, khoảnh khắc gần gũi | Tuấn, Linh |
| 9 | Cảnh nhìn vào quán qua mưa | Cảnh, Linh |
| 10 | Nhóm đối mặt nhau, sự thật vỡ | Cả nhóm |
| 11-24 | (xem chi tiết trong chapters) | ... |

Mỗi chapter nên có:
- 1 establishing shot (location)
- 2-3 character interaction shots
- 1 emotional close-up
