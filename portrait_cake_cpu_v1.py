import os
import math
import random
from PIL import Image
# Import new_session to force CPU execution
from rembg import remove, new_session 

def batch_process_cake(input_dir, output_path):
    # 1. Force the AI model to run on CPU to bypass CUDA 13 errors
    print("Initializing AI Model on CPU...")
    cpu_session = new_session("u2net")
    
    images = []
    if not os.path.exists(input_dir):
        print(f"Error: Directory '{input_dir}' does not exist! Please create it.")
        return

    # Sort files to ensure 001.jpg, 002.jpg order
    file_list = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    
    if not file_list:
        print(f"No images found in '{input_dir}' folder!")
        return

    print(f"Found {len(file_list)} photos. Processing AI background removal...")
    
    for idx, file in enumerate(file_list):
        img_path = os.path.join(input_dir, file)
        try:
            img = Image.open(img_path)
            # Pass the CPU session here explicitly
            no_bg = remove(img, session=cpu_session) 
            
            # Crop out silent transparent padding spaces
            bbox = no_bg.getbbox()
            if bbox:
                no_bg = no_bg.crop(bbox)
            images.append(no_bg)
            print(f"[{idx+1}/{len(file_list)}] Successfully extracted portrait from {file}")
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")
    
    total_pics = len(images)
    print(f"\nAI extraction complete. Building cake layout with {total_pics} portraits...")

    # 2. Create ultra-high-res canvas (3000x3500px)
    canvas_w, canvas_h = 3000, 3500
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    
    # 3. Dynamic Cake Matrix Layering Formulas
    layers = [
        {"y_baseline": 3000, "span_w": 2200, "quota": math.ceil(total_pics * 0.40)},  # Layer 1 (Bottom)
        {"y_baseline": 2300, "span_w": 1700, "quota": math.ceil(total_pics * 0.32)},  # Layer 2 (Middle-Low)
        {"y_baseline": 1600, "span_w": 1200, "quota": math.ceil(total_pics * 0.20)},  # Layer 3 (Middle-High)
        {"y_baseline": 900,  "span_w": 600,  "quota": max(1, total_pics - (math.ceil(total_pics * 0.40) + math.ceil(text_val := total_pics * 0.32) + math.ceil(total_pics * 0.20)))} # Layer 4 (Top Candle Position)
    ]
    
    img_idx = 0
    for layer_num, layer in enumerate(layers):
        count = min(layer["quota"], total_pics - img_idx)
        if count <= 0: break
        
        # Calculate size per portrait to fit the row snugly with a 35% overlap factor
        target_w = int(layer["span_w"] / (max(1, count - 1) * 0.65 + 1))
        target_w = min(target_w, 450)  # Caps maximum size so top portraits don't look giant
        
        for i in range(count):
            if img_idx >= total_pics: break
            p_img = images[img_idx]
            
            # Maintain aspect ratio
            aspect = p_img.height / p_img.width
            target_h = int(target_w * aspect)
            p_resized = p_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            # X positioning
            if count == 1:
                x = int((canvas_w - target_w) / 2)
            else:
                x_start = (canvas_w - layer["span_w"]) / 2
                x = int(x_start + (layer["span_w"] - target_w) * (i / (count - 1)))
            
            # Y positioning + organic layout jitter so they don't sit on a strict line
            jitter = random.randint(-20, 20)
            y = layer["y_baseline"] - target_h + jitter
            
            # Merge onto canvas
            canvas.paste(p_resized, (x, y), p_resized)
            img_idx += 1

    # Save output
    final_output = os.path.abspath(output_path)
    # Convert RGBA to RGB before saving as JPEG
    rgb_canvas = canvas.convert("RGB")
    rgb_canvas.save(final_output, "JPEG", quality=95)
    print(f"\n✨ Success! Your portrait cake collage is saved at:\n👉 {final_output}")

if __name__ == "__main__":
    # Point to your images directory and output name
    batch_process_cake("./input", "./portrait_cake_result.jpg")
