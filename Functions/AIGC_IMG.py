import torch
from diffusers import DiffusionPipeline

device = "mps" if torch.backends.mps.is_available() else "cpu"

pipe = DiffusionPipeline.from_pretrained("stabilityai/", torch_dtype=torch.float16)
pipe.to(device)

prompt = "Astronaut in a jungle, cold color palette, muted colors, detailed, 8k"
image = pipe(prompt).images[0]