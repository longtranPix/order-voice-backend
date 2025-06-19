import json
import re
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name, torch_dtype=torch.float16, device_map="auto"
)
model.eval()


def extract_info_from_text(text: str):
    prompt = f"""
    Bạn là một AI giúp phân tích đơn hàng từ văn bản tiếng Việt.

    Hãy trích xuất **danh sách sản phẩm** dưới dạng **JSON array** (mảng), mỗi sản phẩm có 3 trường:

    - "ten_hang_hoa": tên sản phẩm (ví dụ: "TV Samsung")
    - "so_luong": số lượng (mặc định là 1 nếu không có)
    - "don_gia": đơn giá dạng số nguyên, bao gồm cả số lẻ nếu có (ví dụ: 25100000), nếu không rõ thì để null.

    Chỉ trả về mảng JSON duy nhất, không thêm giải thích, không có markdown, không có ký hiệu ```json.

    Câu ví dụ: "{text}"

    Kết quả:
    """

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.9,
            eos_token_id=tokenizer.eos_token_id,
        )

    result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # --- Làm sạch kết quả ---
    # Tìm đoạn từ dấu `[` đến `]`
    json_match = re.search(r"\[[^\[\]]+\]", result)
    if not json_match:
        return {
            "error": "Không tìm thấy kết quả JSON hợp lệ",
            "raw": result
        }

    json_str = json_match.group(0)

    try:
        parsed = json.loads(json_str)
        return parsed
    except json.JSONDecodeError as e:
        return {
            "error": "Không nghe rõ từ bạn!",
            "raw": json_str,
            "exception": str(e),
        }
