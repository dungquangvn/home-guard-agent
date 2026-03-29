import cv2
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from PIL import Image
import numpy as np
from pathlib import Path
import torch
import torch.nn as nn
from torchvision import models
from torchvision.transforms import v2
from typing import List, Dict

device = 'cuda' if torch.cuda.is_available() else 'cpu'
# device = 'cpu'
dtype = torch.bfloat16 if device == 'cuda' else torch.float32
# dtype = torch.float16

class Predictor(nn.Module):
    def __init__(self, num_age=3, num_view=3, num_others=19):
        super(Predictor, self).__init__()
        self.backbone = models.vit_b_16(weights='DEFAULT')
        in_features = self.backbone.heads.head.in_features
        self.backbone.heads = nn.Identity()

        self.female_head = nn.Linear(in_features, 1) # NhÃ¡nh Gender (BCE)
        self.age_head = nn.Linear(in_features, num_age) # NhÃ¡nh Age (CE)
        self.view_head = nn.Linear(in_features, num_view) # NhÃ¡nh View (CE)
        self.other_head = nn.Sequential(
            nn.Linear(in_features, in_features),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(in_features, num_others) # 19 nhÃ£n cÃ²n láº¡i (BCE)
        )

    def forward(self, x):
        f = self.backbone(x)
        return self.female_head(f), self.age_head(f), self.view_head(f), self.other_head(f)
    
class CaptionGenerator:
    def __init__(self):
        # self.generator_path = Path("models/smollm").resolve()
        # self.generator = AutoModelForCausalLM.from_pretrained(
        #     self.generator_path,
        #     local_files_only=True,
        #     dtype=dtype,
        #     trust_remote_code=True,
        #     device_map=device 
        # )
        # self.tokenizer = AutoTokenizer.from_pretrained(self.generator_path)
        # print("Instantiated caption generator")
        
        self.predictor_state_dict_path = Path("models/predictor.pth").resolve()
        self.predictor_state_dict = torch.load(self.predictor_state_dict_path, map_location=device)
        self.predictor = Predictor().eval().to(device).to(dtype)
        self.predictor.load_state_dict(self.predictor_state_dict) 
        print("Instantiated human attribute predictor")
        
        self.attr_names = ['Female', 'AgeOver60', 'Age18-60', 'AgeLess18', 'Front', 'Side', 'Back', 
            'Hat', 'Glasses', 'HandBag', 'ShoulderBag', 'Backpack', 'HoldObjectsInFront', 
            'ShortSleeve', 'LongSleeve', 'UpperStride', 'UpperLogo', 'UpperPlaid', 
            'UpperSplice', 'LowerStripe', 'LowerPattern', 'LongCoat', 'Trousers', 
            'Shorts', 'Skirt&Dress', 'boots']
        
    def predict_attributes_from_image(
        self, 
        image: np.ndarray, 
    ) -> List[str]:
        tf = v2.Compose([
            v2.ToImage(),
            v2.Resize(size=(224, 224), antialias=True),
            # v2.CenterCrop(size=(224, 224)),
            v2.ToDtype(torch.bfloat16, scale=True),
            v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        image = tf(image)
        image = image.unsqueeze(0).to(device)
        
        with torch.inference_mode():
            female_logits, age_logits, view_logits, other_logits = self.predictor(image)
            
        female_score = torch.sigmoid(female_logits).item()
        age_scores = torch.softmax(age_logits, dim=1).float().cpu().numpy()[0]
        view_scores = torch.softmax(view_logits, dim=1).float().cpu().numpy()[0]
        other_scores = torch.sigmoid(other_logits).float().cpu().numpy()[0]
        # print("=== Logits ===")
        # for name, score in zip(self.attr_names, [female_score] + age_scores.tolist() + view_scores.tolist() + other_scores.tolist()):
        #     print(f"{name}: {score}")
        tags = []

        # Gender
        if female_score > 0.9:
            tags.append("Female")

        # Age (always one)
        age_idx = int(np.argmax(age_scores))
        tags.append(self.attr_names[1 + age_idx])

        # View (always one)
        view_idx = int(np.argmax(view_scores))
        tags.append(self.attr_names[4 + view_idx])

        # Others with grouping rules
        other_names = self.attr_names[7:]
        other_score_map = {name: score for name, score in zip(other_names, other_scores.tolist())}

        group_defs = [
            ["ShortSleeve", "LongSleeve"],
            ["UpperStride", "UpperLogo", "UpperPlaid", "UpperSplice"],
            ["LowerStripe", "LowerPattern"],
            ["Trousers", "Shorts", "Skirt&Dress"],
        ]
        grouped_names = {name for group in group_defs for name in group}

        for group in group_defs:
            best_name = max(group, key=lambda n: other_score_map.get(n, 0.0))
            if other_score_map.get(best_name, 0.0) > 0.5:
                tags.append(best_name)

        for name, score in other_score_map.items():
            if name in grouped_names:
                continue
            if score > 0.5:
                tags.append(name)
        
        if 'Female' not in tags:
            tags.insert(0, 'Male')
        
        return np.array(tags)
    
    def get_caption(self, image: np.ndarray) -> str:
        tags = self.predict_attributes_from_image(image)
        age_text = "aged 18-60" if "Age18-60" in tags else ("over 60 years old" if "AgeOver60" in tags else "under 18 years old")
        if "AgeLess18" in tags:
            subject = "girl" if "Female" in tags else "boy"
        else:
            subject = "woman" if "Female" in tags else "man"

        view_map = {
            "Front": "front",
            "Side": "side",
            "Back": "back",
        }
        view_label = next((x for x in ["Front", "Side", "Back"] if x in tags), None)
        view_str = f", viewed from the {view_map[view_label]}" if view_label else ""

        clothing_map = {
            "ShortSleeve": "short-sleeve top",
            "LongSleeve": "long-sleeve top",
            "UpperStride": "striped top",
            "UpperLogo": "top with a logo",
            "UpperPlaid": "plaid top",
            "UpperSplice": "color-block top",
            "LowerStripe": "striped pants",
            "LowerPattern": "patterned pants",
            "LongCoat": "long coat",
            "Trousers": "trousers",
            "Shorts": "shorts",
            "Skirt&Dress": "skirt or dress",
            "boots": "boots",
        }
        accessories_map = {
            "Hat": "hat",
            "Glasses": "glasses",
            "HandBag": "handbag",
            "ShoulderBag": "shoulder bag",
            "Backpack": "backpack",
        }

        clothing = [clothing_map[t] for t in tags if t in clothing_map]
        accessories = [accessories_map[t] for t in tags if t in accessories_map]

        clothing_str = f", wearing {', '.join(clothing)}" if clothing else ""
        accessories_str = f", carrying {', '.join(accessories)}" if accessories else ""
        hold_str = ", holding an object in front" if "HoldObjectsInFront" in tags else ""

        prompt = f"A {subject} {age_text}{view_str}{clothing_str}{accessories_str}{hold_str}."
        return prompt
    # def generate_caption_from_prompt(self, prompt: str) -> str:
    #     messages = [
    #         {
    #             "role": "user",
    #             "content": prompt,
    #         },
    #     ]
    #     # Táº¡o prompt chuáº©n
    #     template_prompt = self.tokenizer.apply_chat_template(messages, tokenize=False)
    #     print(f"Prompt: {template_prompt}")
    #     inputs = self.tokenizer.encode(template_prompt, return_tensors="pt").to(device)

    #     generated_ids = self.generator.generate(
    #         inputs, 
    #         max_new_tokens=50, 
    #         temperature=0.2, 
    #         top_p=0.9, 
    #         do_sample=True
    #     )
        
    #     # Cáº¯t bá» pháº§n prompt á»Ÿ Ä‘áº§u output
    #     # generated_ids = generated_ids[:, inputs["input_ids"].shape[1]:]
    #     caption = self.tokenizer.decode(generated_ids[0])
        
    #     return caption
    
    # def generate_caption_from_image(self, image: np.ndarray, threshold: float = 0.5):
    #     tags = self.predict_attributes_from_image(image, threshold)
    #     prompt = self.prepare_generator_prompt(tags)
    #     caption = self.generate_caption_from_prompt(prompt)
    #     return caption
      
if __name__ == '__main__':
    image = cv2.imread("data/nguoi_la_frame.jpg", cv2.IMREAD_COLOR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    cg = CaptionGenerator()
    caption = cg.get_caption(image)
    print(f"Caption: {caption}")
