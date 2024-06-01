import os
import torch
from PIL import Image
from model import Model
from utils import CTCLabelConverter, NormalizePAD

def load_model(model_path, char_file):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    with open(char_file, "r", encoding="utf-8") as file:
        characters = ''.join([line.strip() for line in file.readlines()]) + " "
    
    converter = CTCLabelConverter(characters)
    model = Model(num_class=len(converter.character), device=device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    return model, converter, device

def extract_text_from_image(image_path, model, converter, device):
    img = Image.open(image_path).convert('RGB').transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    w, h = img.size
    ratio = w / float(h)
    img = img.resize((int(ratio * 32), 32), Image.Resampling.BICUBIC)
    img = NormalizePAD((1, 32, 400))(img).unsqueeze(0).to(device)
    preds = model(img)
    preds_size = torch.IntTensor([preds.size(1)] * img.shape[0])
    _, preds_index = preds.max(2)
    preds_str = converter.decode(preds_index.data, preds_size.data)[0]
    return preds_str

def extract_text_from_book(book_dir, output_file, model, converter, device):
    with open(output_file, 'w', encoding='utf-8') as file:
        for image_file in sorted(os.listdir(book_dir)):
            image_path = os.path.join(book_dir, image_file)
            text = extract_text_from_image(image_path, model, converter, device)
            file.write(text + "\n")

if __name__ == "__main__":
    books_folder = 'booksn'
    text_output_folder = 'extracted_text'
    model_path = 'models/UTRNet/best_norm_ED.pth'
    char_file = 'models/UTRNet/UrduGlyphs.txt'
    
    model, converter, device = load_model(model_path, char_file)
    
    for book_dir in sorted(os.listdir(books_folder)):
        book_path = os.path.join(books_folder, book_dir)
        output_file = os.path.join(text_output_folder, f'book{book_dir}.txt')
        extract_text_from_book(book_path, output_file, model, converter, device)
