import os
import json
from google import genai
from google.genai import types
from PIL import Image
import io

class ImageGenerator:
    def __init__(self, settings_path="config/settings.json"):
        settings = {}
        if os.path.exists(settings_path):
            with open(settings_path, "r") as f:
                settings = json.load(f)

        self.api_key = (
            os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or settings.get("gemini_api_key")
        )
        configured_model = os.environ.get("GOOGLE_IMAGE_MODEL") or settings.get("google_image_model")
        self.image_models = [
            model for model in [
                configured_model,
                "imagen-4.0-generate-001",
                "imagen-4.0-fast-generate-001",
            ]
            if model
        ]
        self.gemini_image_models = ["gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview", "gemini-2.5-flash-image"]
        self.client = genai.Client(api_key=self.api_key) if self.api_key and self.api_key != "YOUR_API_KEY_HERE" else None

    def generate_image(self, prompt_subject, output_path):
        if not self.client:
            print("⚠️ Google AI API 키가 설정되지 않아 이미지 생성을 건너뜁니다.", flush=True)
            return False

        prompt = (
            "Create a cinematic 16:9 editorial hero image with high detail, "
            "premium digital art style, subtle cyberpunk lighting, no text, no logo. "
            f"Topic: {prompt_subject}"
        )
        print(f"🎨 Google AI 이미지 생성을 시작합니다: {prompt_subject}", flush=True)
        
        last_error = None
        for model in self.image_models:
            try:
                print(f"  - 이미지 모델 시도: {model}", flush=True)
                response = self.client.models.generate_images(
                    model=model,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="16:9",
                        output_mime_type="image/jpeg"
                    )
                )

                for generated_image in response.generated_images:
                    image = Image.open(io.BytesIO(generated_image.image.image_bytes))
                    # jpeg으로 저장되지만 사용자 경로의 확장자를 유지
                    image.save(output_path)
                    print(f"✅ Google 이미지 생성 및 저장 완료: {output_path}", flush=True)
                    return True

                print(f"⚠️ 이미지가 응답에 포함되지 않았습니다: {model}", flush=True)
            except Exception as e:
                last_error = e
                message = str(e)
                if "paid plans" in message or "billing" in message.lower():
                    print(f"⚠️ 이미지 모델 사용 불가: {model} - Google AI Studio 결제/유료 플랜이 필요합니다.", flush=True)
                else:
                    print(f"⚠️ 이미지 모델 실패: {model} - {e}", flush=True)

        for model in self.gemini_image_models:
            try:
                print(f"  - Gemini 이미지 모델 시도: {model}", flush=True)
                response = self.client.models.generate_content(
                    model=model,
                    contents=[prompt],
                )
                for part in response.parts:
                    if getattr(part, "inline_data", None) is not None:
                        if hasattr(part, "as_image"):
                            image = part.as_image()
                        else:
                            image = Image.open(io.BytesIO(part.inline_data.data))
                        image.save(output_path)
                        print(f"✅ Gemini 이미지 생성 및 저장 완료: {output_path}", flush=True)
                        return True
            except Exception as e:
                last_error = e
                message = str(e)
                if "RESOURCE_EXHAUSTED" in message or "quota" in message.lower():
                    print(f"⚠️ Gemini 이미지 모델 쿼터 초과: {model} - Google AI Studio 사용량/결제 한도를 확인해야 합니다.", flush=True)
                else:
                    print(f"⚠️ Gemini 이미지 모델 실패: {model} - {e}", flush=True)

        print(f"❌ Google 이미지 생성 오류: 사용 가능한 이미지 모델을 찾지 못했습니다. 마지막 오류: {last_error}", flush=True)
        return False
