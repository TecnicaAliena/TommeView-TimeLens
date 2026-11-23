"""Convert the selected artwork to the Windows multi-resolution application icon."""
from pathlib import Path
from PIL import Image


def main():
    root = Path(__file__).resolve().parent
    with Image.open(root / 'assets/icon-proposals/02-timeline.png') as source:
        source.convert('RGBA').save(root / 'assets/tommeview.ico', format='ICO',
                                   sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])


if __name__ == '__main__':
    main()
