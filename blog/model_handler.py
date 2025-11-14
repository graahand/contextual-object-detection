import torch
from transformers import AutoProcessor, AutoModelForVision2Seq
from PIL import Image
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)

# Set PyTorch memory allocation settings to reduce fragmentation
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

class ModelHandler:
    _instance = None
    _model = None
    _processor = None
    _use_cuda = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.initialize_model()

    def initialize_model(self):
        try:
            DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
            self._use_cuda = DEVICE == "cuda"
            if self._processor is None:
                self._processor = AutoProcessor.from_pretrained("HuggingFaceTB/SmolVLM-500M-Instruct")
            if self._model is None:
                self._model = AutoModelForVision2Seq.from_pretrained(
                    "HuggingFaceTB/SmolVLM-256M-Instruct",
                    torch_dtype=torch.bfloat16 if self._use_cuda else torch.float32,
                    _attn_implementation="flash_attention_2" if self._use_cuda else "eager",
                ).to(DEVICE)
            logger.info(f"Successfully loaded SmolVLM model on {DEVICE}")
        except Exception as e:
            logger.error(f"Error loading SmolVLM model: {e}")
            raise

    def _prepare_inputs(self, image, question_text):
        # Support image path or PIL Image
        if isinstance(image, str):
            image = Image.open(image)
        if image.mode != "RGB":
            image = image.convert("RGB")
        DEVICE = "cuda" if self._use_cuda else "cpu"
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": question_text},
                ]
            },
        ]
        prompt = self._processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self._processor(text=prompt, images=[image], return_tensors="pt").to(DEVICE)
        return inputs

    def generate_short_caption(self, image):
        """Generate a short caption for the image."""
        try:
            if self._use_cuda:
                torch.cuda.empty_cache()
            inputs = self._prepare_inputs(image, "Describe the image in detail.")
            generated_ids = self._model.generate(**inputs, max_new_tokens=50)
            generated_texts = self._processor.batch_decode(generated_ids, skip_special_tokens=True)
            caption = generated_texts[0]
            logger.info(f"Generated short caption: {caption}")
            return caption
        except Exception as e:
            logger.error(f"Error generating short caption: {e}")
            raise

    def generate_normal_caption(self, image):
        """Generate a descriptive caption for the image."""
        try:
            if self._use_cuda:
                torch.cuda.empty_cache()
            inputs = self._prepare_inputs(image, "Describe this image in detail.")
            generated_ids = self._model.generate(**inputs, max_new_tokens=100)
            generated_texts = self._processor.batch_decode(generated_ids, skip_special_tokens=True)
            caption = generated_texts[0]
            logger.info(f"Generated normal caption: {caption}")
            return caption
        except Exception as e:
            logger.error(f"Error generating normal caption: {e}")
            raise

    def process_query(self, image, query="What is in this image?"):
        """Process a query about the image."""
        try:
            if self._use_cuda:
                torch.cuda.empty_cache()
            inputs = self._prepare_inputs(image, query)
            generated_ids = self._model.generate(**inputs, max_new_tokens=100)
            generated_texts = self._processor.batch_decode(generated_ids, skip_special_tokens=True)
            answer = generated_texts[0]
            logger.info(f"Generated query response: {answer}")
            return answer
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise 