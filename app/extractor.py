# # import json
# # import re
# # from transformers import AutoModelForCausalLM, AutoTokenizer
# # import torch

# # model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# # tokenizer = AutoTokenizer.from_pretrained(model_name)
# # model = AutoModelForCausalLM.from_pretrained(
# #     model_name, torch_dtype=torch.float16, device_map="auto"
# # )
# # model.eval()


# # def extract_info_from_text(text: str):
# #     prompt = f"""
# #     Bạn là một AI giúp phân tích đơn hàng từ văn bản tiếng Việt.

# #     Hãy trích xuất **danh sách sản phẩm** dưới dạng **JSON array** (mảng), mỗi sản phẩm có 3 trường:

# #     - "ten_hang_hoa": tên sản phẩm (ví dụ: "TV Samsung")
# #     - "so_luong": số lượng (mặc định là 1 nếu không có)
# #     - "don_gia": đơn giá dạng số nguyên, bao gồm cả số lẻ nếu có (ví dụ: 25100000), nếu không rõ thì để null.

# #     Chỉ trả về mảng JSON duy nhất, không thêm giải thích, không có markdown, không có ký hiệu ```json.

# #     Câu ví dụ: "{text}"

# #     Kết quả:
# #     """

# #     inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

# #     with torch.no_grad():
# #         outputs = model.generate(
# #             **inputs,
# #             max_new_tokens=256,
# #             temperature=0.7,
# #             top_p=0.9,
# #             eos_token_id=tokenizer.eos_token_id,
# #         )

# #     result = tokenizer.decode(outputs[0], skip_special_tokens=True)

# #     # --- Làm sạch kết quả ---
# #     # Tìm đoạn từ dấu `[` đến `]`
# #     json_match = re.search(r"\[[^\[\]]+\]", result)
# #     if not json_match:
# #         return {
# #             "error": "Không tìm thấy kết quả JSON hợp lệ",
# #             "raw": result
# #         }

# #     json_str = json_match.group(0)

# #     try:
# #         parsed = json.loads(json_str)
# #         return parsed
# #     except json.JSONDecodeError as e:
# #         return {
# #             "error": "Không nghe rõ từ bạn!",
# #             "raw": json_str,
# #             "exception": str(e),
# #         }

# # import httpx

# # LLAMA_SERVER_URL = "http://127.0.0.1:8080/completion"

# # def extract_info_from_text(text: str):
# #     prompt = f"""
# # Bạn là một AI phân tích đơn hàng tiếng Việt.

# # Hãy trích xuất một object JSON duy nhất với 3 trường:
# # - "ten_hang_hoa": tên sản phẩm (ví dụ: "TV Samsung")
# # - "so_luong": số lượng sản phẩm, là số nguyên. Nếu không có, mặc định là 1.
# # - "don_gia": đơn giá mỗi sản phẩm, là số nguyên. Phải hiểu đúng các cách viết như:
# #   - "năm mươi triệu" = 50000000
# #   - "hai triệu rưỡi" = 2500000
# #   - "25 triệu 100 nghìn" = 25100000

# # **Chỉ trả về một object JSON duy nhất**, không có giải thích, không có markdown, không có ` ``` `, không có chữ thừa.

# # Ví dụ câu: "{text}"

# # Kết quả:
# # """

# #     payload = {
# #         "prompt": prompt.strip(),
# #         "temperature": 0.1,
# #         "n_predict": 256,
# #         "stop": ["</s>"]
# #     }

# #     try:
# #         response = httpx.post(LLAMA_SERVER_URL, json=payload, timeout=60)
# #         response.raise_for_status()
# #         content = response.json()
# #         return {"raw": content["content"].strip()}
# #     except Exception as e:
# #         return {"error": str(e)}


# import httpx
# import os
# import json
# import re

# OPENROUTER_API_KEY = os.getenv("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")  # Hoặc set cứng

# def extract_info_from_text(text: str):
#     prompt = f"""
# Bạn là một trợ lý AI.

# Hãy phân tích câu sau và trích xuất ra danh sách sản phẩm dưới dạng **JSON array**, mỗi sản phẩm gồm:
# - "ten_hang_hoa": tên sản phẩm
# - "so_luong": số lượng sản phẩm (mặc định 1 nếu không ghi rõ)
# - "don_gia": đơn giá sản phẩm (là số nguyên, có thể có số lẻ, ví dụ: 25100000). Nếu không rõ thì để null.

# Chỉ trả về mảng JSON hợp lệ, không có lời giải thích hay ký hiệu thừa.

# Câu: "{text}"

# Kết quả:
# """

#     headers = {
#         "Authorization": f"Bearer {OPENROUTER_API_KEY}",
#         "HTTP-Referer": "http://localhost",  # Có thể đặt tên domain app bạn
#         "X-Title": "extract-bill-vietnamese"
#     }

#     body = {
#         "model": "deepseek-chat",
#         "messages": [
#             {"role": "user", "content": prompt.strip()}
#         ],
#         "temperature": 0.2,
#         "max_tokens": 512
#     }

#     try:
#         response = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body, timeout=60)
#         response.raise_for_status()
#         reply = response.json()["choices"][0]["message"]["content"]

#         # Tìm JSON array
#         match = re.search(r"\[.*\]", reply, re.DOTALL)
#         if match:
#             return json.loads(match.group(0))
#         else:
#             return {"error": "Không tìm thấy mảng JSON hợp lệ", "raw": reply}
#     except Exception as e:
#         return {"error": str(e)}


import requests
import json
from app.core.config import settings

def extract_info_from_text(text: str):
    try:

        response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
            "messages": [
            {
                "role": "user",
                "content": f"""
                            Bạn là một AI hỗ trợ phân tích hóa đơn từ văn bản tiếng Việt.

                            Yêu cầu:
                            - Phân tích câu sau và trích xuất thành **một mảng JSON**, mỗi phần tử là một object có đúng 3 trường:
                            - "ten_hang_hoa": tên hàng hoá
                            - "so_luong": số lượng (mặc định là 1 nếu không ghi rõ)
                            - "don_gia": đơn giá của **một đơn vị hàng hóa**, là số nguyên (có thể ghi bằng số hoặc chữ, ví dụ: "2 triệu 180 nghìn" = 2180000). Nếu không rõ thì để `null`.

                            - Chuyển đổi giá tiền ghi bằng chữ sang dạng số nguyên chính xác (ví dụ: "năm mươi triệu" = 50000000, "hai triệu một trăm tám mươi nghìn" = 2180000)

                            - Tuyệt đối **không nhân số lượng với đơn giá**. Mỗi object chỉ thể hiện đơn giá cho 1 đơn vị.

                            - Chỉ trả về **một mảng JSON hợp lệ**, không có giải thích, không markdown, không ký hiệu ```json hoặc ký hiệu dư thừa.

                            Câu cần phân tích:
                            "{text}"
                """
            }
            ],
            
        })
        )

        response.raise_for_status()
        data = response.json()
        result = data["choices"][0]["message"]["content"]

        # Clean markdown if any slipped in
        result = result.strip().replace("```json", "").replace("```", "").strip()

        return json.loads(result)

    except Exception as e:
        return {"error": str(e)}
