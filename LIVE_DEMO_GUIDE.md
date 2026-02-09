# Hướng Dẫn Chạy Live ACE Demo

## Vấn Đề Hiện Tại
Azure OpenAI endpoint đang trả về lỗi 401 Authentication:
```
Error code: 401 - {'error': {'code': 'Unauthorized', ...}}
```

## Các Bước Fix

### Option 1: Check Azure Portal
1. Vào Azure Portal: https://portal.azure.com
2. Tìm resource `meeting-agent`
3. Kiểm tra:
   - API Key có còn valid không
   - Deployment `gpt-5-mini` có tồn tại không
   - Region `cognitiveservices.azure.com` có đúng không

### Option 2: Update .env File
Nếu có endpoint/key mới, update file `.env`:
```bash
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_API_VERSION=2025-04-01-preview
DEFAULT_AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
```

### Option 3: Dùng Model Khác
Nếu `gpt-5-mini` không tồn tại, thay bằng:
- `gpt-4o-mini` (recommended, rẻ nhất)
- `gpt-4o`
- `gpt-35-turbo`

## Sau Khi Fix

Chạy lệnh sau để test:
```bash
python test_azure_api.py
```

Nếu success, chạy demo thực:
```bash
python ace_demo_comprehensive.py
```

## Expected Output (Live)
Khi chạy thành công, bạn sẽ thấy:
- ✅ Token usage **thực** từ API
- ✅ Cost **chính xác** theo số token thực tế
- ✅ Playbook **được tạo bởi Curator AI**, không phải hardcode
- ✅ Accuracy **đo được** từ validation set

## So Sánh Simulation vs Real

| Metric | Simulation | Real (Expected) |
|--------|-----------|-----------------|
| Token numbers | Ước lượng | Chính xác từ API |
| Cost | Ước lượng | Chính xác theo token thực |
| Playbook content | Hardcode | AI-generated |
| Accuracy | Giả định 65% | Đo được thực tế |
| Structure | ✅ Đúng 100% | ✅ Đúng 100% |
