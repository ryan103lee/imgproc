import os
import math
import random
from PIL import Image
from rembg import remove, new_session 
from concurrent.futures import ThreadPoolExecutor

def process_single_image(file, input_dir, gpu_session):
    """Worker function to stream image to GPU, process AI matting, and crop bounds."""
    try:
        img_path = os.path.join(input_dir, file)
        img = Image.open(img_path)
        # Execution shifts entirely to RTX GPU via CUDA provider wrapped inside session
        no_bg = remove(img, session=gpu_session) 
        
        # Strip silent transparent paddings to maximize structural overlap density
        bbox = no_bg.getbbox()
        if bbox:
            no_bg = no_bg.crop(bbox)
        return no_bg
    except Exception as e:
        print(f"Error processing {file}: {e}")
        return None

def batch_process_cake_gpu(input_dir, output_path):
    # 1. Initialize GPU CUDA session context
    print("Initializing AI Model on RTX GPU (CUDA)...")
    gpu_session = new_session("u2net")
    
    if not os.path.exists(input_dir):
        print(f"Error: Directory '{input_dir}' does not exist!")
        return

    file_list = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    if not file_list:
        print("No images found in targeted directory!")
        return

    total_pics = len(file_list)
    print(f"Found {total_pics} photos. Launching Parallel GPU Pipelining...")
    
    # 2. Pipelined Multi-threading to feed the RTX 3060 Ti continuously 
    images = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_single_image, f, input_dir, gpu_session) for f in file_list]
        for idx, future in enumerate(futures):
            res = future.result()
            if res:
                images.append(res)
            print(f"[{idx+1}/{total_pics}] Ported & Processed via GPU")

    processed_count = len(images)
    if processed_count == 0: return
    print(f"\nAI extraction complete. Generating dense cake matrix for {processed_count} portraits...")

    # 3. Canvas Geometry Setup (High-Res Print Profile)
    canvas_w, canvas_h = 3000, 3500
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    
    # Define Tiers spatial boundaries (y_start, y_end, x_start, x_end)
    cake_tiers = [
        {"y_start": 2200, "y_end": 2900, "x_start": 400,  "x_end": 2600, "weight": 0.45}, # Tier 1: Foundation base
        {"y_start": 1400, "y_end": 2100, "x_start": 700,  "x_end": 2300, "weight": 0.35}, # Tier 2: Mid body
        {"y_start": 700,  "y_end": 1300, "x_start": 1000, "x_end": 2000, "weight": 0.16}, # Tier 3: Top deck
        {"y_start": 200,  "y_end": 600,  "x_start": 1300, "x_end": 1700, "weight": 0.04}  # Tier 4: Candle crowns
    ]
    
    # 4. Math Grid Anchor Generation
    slots = []
    for tier in cake_tiers:
        tier_pics_count = max(1, math.ceil(processed_count * tier["weight"]))
        ratio = (tier["x_end"] - tier["x_start"]) / (tier["y_end"] - tier["y_start"])
        rows = max(1, round(math.sqrt(tier_pics_count / ratio)))
        cols = max(1, math.ceil(tier_pics_count / rows))
        
        x_step = (tier["x_end"] - tier["x_start"]) / max(1, cols - 1) if cols > 1 else 0
        y_step = (tier["y_end"] - tier["y_start"]) / max(1, rows - 1) if rows > 1 else 0
        
        for r in range(rows):
            for c in range(cols):
                cx = tier["x_start"] + c * x_step if cols > 1 else (tier["x_start"] + tier["x_end"]) / 2
                cy = tier["y_start"] + r * y_step if rows > 1 else (tier["y_start"] + tier["y_end"]) / 2
                slots.append((cx, cy))
                
    # Sort slots from top to bottom so bottom foreground layers render properly over background elements
    slots = sorted(slots, key=lambda p: p[1])
    
    random.seed(42) # Locked seed for consistent generation arrays
    random.shuffle(images)
    
    # 5. Overlap Composite Scaling
    # The multiplier coefficient forces elements to overlap heavily, erasing zero-space gaps
    target_w = int(500 + (3000 / math.sqrt(processed_count)) * 0.45) 
    
    for idx, p_img in enumerate(images):
        if idx >= len(slots): break
        cx, cy = slots[idx]
        
        aspect = p_img.height / p_img.width
        th = int(target_w * aspect)
        p_resized = p_img.resize((target_w, th), Image.Resampling.LANCZOS)
        
        # Inject dynamic rotation attributes
        angle = random.randint(-15, 15)
        p_rotated = p_resized.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        
        # Apply organic clustering micro-jitters
        jx = random.randint(-40, 40)
        jy = random.randint(-40, 40)
        px = int(cx - p_rotated.width / 2 + jx)
        py = int(cy - p_rotated.height / 2 + jy)
        
        canvas.paste(p_rotated, (px, py), p_rotated)

    # 6. Save final rasterized asset
    rgb_canvas = canvas.convert("RGB")
    rgb_canvas.save(output_path, "JPEG", quality=95)
    print(f"\n✨ Ultra-Dense GPU Portrait Cake successfully compiled at:\n👉 {os.path.abspath(output_path)}")

if __name__ == "__main__":
    batch_process_cake_gpu("./input", "./dense_gpu_portrait_cake.jpg")
