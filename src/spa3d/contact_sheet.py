from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _font(size):
    path = Path(r"C:\Windows\Fonts\msyh.ttc")
    return ImageFont.truetype(path, size) if path.exists() else ImageFont.load_default()


def _fit(image, box):
    copy = image.copy()
    copy.thumbnail(box, Image.Resampling.LANCZOS)
    return copy


def build_contact_sheet(left_path, right_path, output_path, left_label, right_label):
    with Image.open(left_path) as left_source, Image.open(right_path) as right_source:
        left = _fit(left_source.convert("RGB"), (980, 551))
        right = _fit(right_source.convert("RGB"), (980, 551))
        canvas = Image.new("RGB", (2000, 667), (242, 243, 241))
        canvas.paste(left, (0, 116))
        canvas.paste(right, (1000, 116))
        draw = ImageDraw.Draw(canvas)
        draw.text((30, 22), left_label, font=_font(30), fill=(45, 48, 46))
        draw.text((1030, 22), right_label, font=_font(30), fill=(45, 48, 46))
        draw.line((1000, 0, 1000, 667), fill=(202, 204, 201), width=2)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path)
