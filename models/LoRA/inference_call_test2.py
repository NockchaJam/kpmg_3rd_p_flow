import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import json
import os

class InferenceModel1:
    def __init__(self, model_path, adapter_path, max_token_length=4096, device="cuda"):
        """
        Initialize the model and tokenizer with given paths.

        Args:
            model_path (str): Path to the pretrained model.
            adapter_path (str): Path to the LoRA adapter.
            max_token_length (int): Maximum token length for the tokenizer.
            device (str): Device to run the model on ('cuda' or 'cpu').
        """
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")

        # Load model and tokenizer
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        # Load and merge LoRA adapter
        self.model = PeftModel.from_pretrained(self.model, adapter_path)
        self.model = self.model.merge_and_unload()

        # Configure tokenizer
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        self.tokenizer.model_max_length = max_token_length

        self.model.eval()
        self.model.to(self.device)

    def create_prompt(self, features):
        """
        Create a formatted prompt based on input features.

        Args:
            features (dict): Dictionary of input features.

        Returns:
            str: Generated prompt.
        """
        prompt_template = (
            "당신은 대한민국 경상북도 경산시 부동산 전문가입니다. "
            "다음 입력정보를 보고 판단하여 공실 우선순위에 대한 분석 결과를 생성하세요.\n"
            "### 입력 정보:\n{features}\n\n### 분석 결과:\n"
        )
        features_json = json.dumps(features, ensure_ascii=False, indent=2)
        return prompt_template.format(features=features_json)

    def infer_single(self, features):
        """
        Perform inference for a single input.

        Args:
            features (dict): Input features (e.g., {"num_of_company": [...], "num_of_large": [...], ...}).

        Returns:
            str: Generated response.
        """
        prompt = (
            "당신은 대한민국 경상북도 경산시 부동산 전문가입니다. "
            "다음 입력정보를 보고 판단하여 공실 우선순위에 대한 분석 결과를 생성하세요.\n"
            f"### 입력 정보:\n{json.dumps(features, ensure_ascii=False, indent=2)}\n\n### 분석 결과:\n"
        )
        print(f"Generated prompt: {prompt}")  # 생성된 프롬프트 확인
        inputs = self.tokenizer([prompt], return_tensors="pt", padding=True, return_token_type_ids=False).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=300,
                num_beams=5,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
                repetition_penalty=1.2
            )
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Model output: {result}")  # 모델 출력 확인
        response = result[len(prompt):].strip() or "No meaningful response generated"
        return response

    def infer_batch(self, batch_features):
        """
        Perform inference for a batch of inputs.

        Args:
            batch_features (list): List of input features dictionaries.

        Returns:
            list: List of generated responses.
        """
        prompts = [self.create_prompt(features) for features in batch_features]
        inputs = self.tokenizer([prompt], return_tensors="pt", padding=True, return_token_type_ids=False).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=300,
                num_beams=5,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
                repetition_penalty=1.2
            )
        results = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)

        responses = []
        for prompt, result in zip(prompts, results):
            response = result[len(prompt):].strip()
            responses.append(response)

        return responses
    

class InferenceModel2:
    def __init__(self, model_path, adapter_path, max_token_length=4096, device="cuda"):
        """
        Initialize the model and tokenizer with given paths.

        Args:
            model_path (str): Path to the pretrained model.
            adapter_path (str): Path to the LoRA adapter.
            max_token_length (int): Maximum token length for the tokenizer.
            device (str): Device to run the model on ('cuda' or 'cpu').
        """
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")

        # Load model and tokenizer
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        # Load and merge LoRA adapter
        self.model = PeftModel.from_pretrained(self.model, adapter_path)
        self.model = self.model.merge_and_unload()

        # Configure tokenizer
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        self.tokenizer.model_max_length = max_token_length

        self.model.eval()
        self.model.to(self.device)

    def create_prompt(self, features):
        """
        Create a formatted prompt based on input features.

        Args:
            features (dict): Dictionary of input features.

        Returns:
            str: Generated prompt.
        """
        prompt_template = (
            "당신은 대한민국 경상북도 경산시에서 15년 이상 경력을 쌓은 창업 전문 컨설턴트입니다."
            "다음 입력정보는 입점하고자 하는 공실 주변 최근접 3개의 점포들 데이터입니다. "
            "이 데이터를 기반으로 해당 위치에서 성공 가능성이 높은 업종을 평가하고, 공실의 장점과 경쟁력을 분석합니다. "
            "이를 바탕으로 합리적인 근거를 논리적으로 제시하며, 필요한 경우 관련 수치를 명확히 명시합니다. "
            "다음 입력정보에 따라 적절한 분석 결과를 생성하세요.\n"
            "### 입력 정보:\n{features}\n\n### 분석 결과:\n"
            )
        features_json = json.dumps(features, ensure_ascii=False, indent=2)
        return prompt_template.format(features=features_json)

    def infer_single(self, features):
        """
        Perform inference for a single input.

        Args:
            features (dict): Input features (e.g., {"num_of_company": [...], "num_of_large": [...], ...}).

        Returns:
            str: Generated response.
        """
        prompt = (
            "당신은 대한민국 경상북도 경산시 부동산 전문가입니다. "
            "다음 입력정보를 보고 판단하여 공실 우선순위에 대한 분석 결과를 생성하세요.\n"
            f"### 입력 정보:\n{json.dumps(features, ensure_ascii=False, indent=2)}\n\n### 분석 결과:\n"
        )
        print(f"Generated prompt: {prompt}")  # 생성된 프롬프트 확인
        inputs = self.tokenizer([prompt], return_tensors="pt", padding=True, return_token_type_ids=False).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=300,
                num_beams=5,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
                repetition_penalty=1.2
            )
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Model output: {result}")  # 모델 출력 확인
        response = result[len(prompt):].strip() or "No meaningful response generated"
        return response

    def infer_batch(self, batch_features):
        """
        Perform inference for a batch of inputs.

        Args:
            batch_features (list): List of input features dictionaries.

        Returns:
            list: List of generated responses.
        """
        prompts = [self.create_prompt(features) for features in batch_features]
        inputs = self.tokenizer([prompt], return_tensors="pt", padding=True, return_token_type_ids=False).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=300,
                num_beams=5,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
                repetition_penalty=1.2
            )
        results = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)

        responses = []
        for prompt, result in zip(prompts, results):
            response = result[len(prompt):].strip()
            responses.append(response)

        return responses

