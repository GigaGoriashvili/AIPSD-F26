"""Draw the four synthetic test posters with Pillow. No people, no logos.

    python make_posters.py

clean.png         crisp poster, every field readable
torn.png          same poster, date hidden under a torn-paper shape, low contrast
ambiguous.png     two dates on one poster, room printed as B2O4 (letter O)
not-an-event.png  a quiet hours notice, not an event
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

W, H = 800, 1100
OUT = Path(__file__).parent / "posters"


def font(size: int):
    return ImageFont.load_default(size=size)


def base(bg, fg):
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    # a few flat shapes so it reads as a poster, not a form
    d.ellipse([520, -120, 900, 260], fill=fg)
    d.rectangle([0, H - 160, W, H], fill=fg)
    return img, d


def build_night(bg, fg, text, accent):
    img, d = base(bg, fg)
    d.text((60, 120), "OPEN BUILD", font=font(96), fill=text)
    d.text((60, 220), "NIGHT", font=font(96), fill=text)
    d.text((60, 360), "Bring a half-finished project.", font=font(34), fill=text)
    d.text((60, 404), "Leave with a working one.", font=font(34), fill=text)
    d.text((60, 560), "Thursday 2026-10-22", font=font(52), fill=accent)
    d.text((60, 640), "18:00", font=font(52), fill=accent)
    d.text((60, 740), "Room B204", font=font(52), fill=accent)
    d.text((60, 980), "Robotics Club", font=font(40), fill=bg)
    return img


def clean():
    return build_night(bg=(255, 243, 224), fg=(230, 90, 40), text=(20, 20, 30), accent=(200, 50, 30))


def torn():
    img = build_night(bg=(236, 230, 220), fg=(190, 150, 130), text=(110, 105, 100), accent=(140, 100, 90))
    d = ImageDraw.Draw(img)
    rnd = random.Random(7)
    # torn paper strip over the date line: jagged top and bottom edges
    top = [(0, 540)] + [(x, 540 + rnd.randint(-18, 18)) for x in range(40, W, 40)] + [(W, 540)]
    bottom = [(W, 625)] + [(x, 625 + rnd.randint(-18, 18)) for x in range(W - 40, 0, -40)] + [(0, 625)]
    d.polygon(top + bottom, fill=(250, 248, 244))
    d.line(top, fill=(205, 200, 194), width=3)
    d.line(bottom, fill=(205, 200, 194), width=3)
    img = ImageEnhance.Contrast(img).enhance(0.55)
    return img


def ambiguous():
    img, d = base((22, 28, 48), (70, 110, 200))
    txt = (235, 238, 250)
    d.text((60, 110), "FILM NIGHT", font=font(100), fill=txt)
    d.text((60, 230), "Student Cinema Society", font=font(36), fill=txt)
    d.text((60, 420), "Oct 22", font=font(64), fill=(255, 200, 80))
    d.line([(60, 455), (280, 455)], fill=(255, 90, 90), width=5)
    d.text((60, 520), "Rescheduled: Oct 29", font=font(56), fill=(255, 120, 120))
    d.text((60, 660), "20:00", font=font(56), fill=txt)
    d.text((60, 760), "Room B2O4", font=font(56), fill=txt)      # letter O, not zero
    d.text((60, 980), "Free popcorn", font=font(40), fill=(22, 28, 48))
    return img


def not_an_event():
    img = Image.new("RGB", (W, H), (245, 245, 240))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, W - 40, H - 40], outline=(40, 40, 40), width=6)
    d.text((80, 140), "QUIET HOURS", font=font(96), fill=(30, 30, 30))
    d.text((80, 300), "Library", font=font(60), fill=(60, 60, 60))
    d.text((80, 420), "22:00 to 08:00", font=font(60), fill=(60, 60, 60))
    d.text((80, 600), "Please keep noise down.", font=font(44), fill=(60, 60, 60))
    d.text((80, 660), "Group rooms are available", font=font(36), fill=(90, 90, 90))
    d.text((80, 706), "on the second floor.", font=font(36), fill=(90, 90, 90))
    d.text((80, 980), "Library Services", font=font(32), fill=(120, 120, 120))
    return img


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, fn in {"clean": clean, "torn": torn, "ambiguous": ambiguous, "not-an-event": not_an_event}.items():
        fn().save(OUT / f"{name}.png")
        print("wrote", OUT / f"{name}.png")
