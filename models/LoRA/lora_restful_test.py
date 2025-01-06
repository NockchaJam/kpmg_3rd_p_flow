from flask import Flask, request, jsonify, render_template_string
from inference_call_test2 import InferenceModel1  # 위에서 만든 InferenceModel 클래스를 import
from inference_call_test2 import InferenceModel2
import os
import json
import urllib.parse

# Flask 객체 생성
app = Flask(__name__)

# 모델 경로 설정
MODEL_PATH = "EleutherAI/polyglot-ko-1.3b"
ADAPTER_PATH1 = "/workspace/LoRA1/outputs/polyglot-ko-1.3b/test/final"
ADAPTER_PATH2 = "/workspace/LoRA2/outputs/polyglot-ko-1.3b/test/final"


# 모델 로드
my_model1 = InferenceModel1(model_path=MODEL_PATH, adapter_path=ADAPTER_PATH1)
my_model2 = InferenceModel2(model_path=MODEL_PATH, adapter_path=ADAPTER_PATH2)



# POST 엔드포인트 정의
@app.route("/ma/analyze1", methods=["POST"])
def analyze():
    try:
        # URL 디코딩
        raw_input = request.get_data(as_text=True).strip()
        decoded_input = urllib.parse.unquote(raw_input)
        print(f"Decoded input data: {decoded_input}")

        # `+` 기호 제거
        sanitized_input = decoded_input.replace("+", "")
        print(f"Sanitized input data: {sanitized_input}")

        # JSON 데이터로 변환
        if sanitized_input.startswith("input_data="):
            json_str = sanitized_input.replace("input_data=", "")
            input_json = json.loads(json_str)
        else:
            input_json = json.loads(sanitized_input)
        print(f"Parsed JSON input: {input_json}")

        # 모델 추론
        response = my_model1.infer_single(input_json)
        print(f"Generated response: {response}")
        return jsonify({"result": response}), 200

    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON format: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# POST 엔드포인트 정의
@app.route("/ma/analyze2", methods=["POST"])
def analyze():
    try:
        # URL 디코딩
        raw_input = request.get_data(as_text=True).strip()
        decoded_input = urllib.parse.unquote(raw_input)
        print(f"Decoded input data: {decoded_input}")

        # `+` 기호 제거
        sanitized_input = decoded_input.replace("+", "")
        print(f"Sanitized input data: {sanitized_input}")

        # JSON 데이터로 변환
        if sanitized_input.startswith("input_data="):
            json_str = sanitized_input.replace("input_data=", "")
            input_json = json.loads(json_str)
        else:
            input_json = json.loads(sanitized_input)
        print(f"Parsed JSON input: {input_json}")

        # 모델 추론
        response = my_model2.infer_single(input_json)
        print(f"Generated response: {response}")
        return jsonify({"result": response}), 200

    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON format: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Flask 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5444, debug=True)






