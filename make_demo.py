from pathlib import Path
import cv2
import numpy as np


def generate():
    folder = Path(__file__).parent / 'demo'
    folder.mkdir(exist_ok=True)
    output = folder / 'demo.avi'
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*'MJPG'), 30, (960, 540))
    if not writer.isOpened():
        raise RuntimeError('Impossibile creare il video dimostrativo')
    for frame in range(600):
        image = np.full((540, 960, 3), (31, 27, 23), dtype=np.uint8)
        for x in range(0, 960, 80):
            cv2.line(image, (x, 130), (x, 445), (62, 58, 51), 1)
        for y in range(130, 446, 63):
            cv2.line(image, (0, y), (959, y), (62, 58, 51), 1)
        cv2.putText(image, 'TOMMEVIEW / VIDEO TEST', (35, 57), cv2.FONT_HERSHEY_SIMPLEX, 1, (220, 235, 240), 2, cv2.LINE_AA)
        cv2.putText(image, f'FRAME {frame:04d}     {frame / 30:06.3f} s', (35, 105), cv2.FONT_HERSHEY_SIMPLEX, .75, (170, 180, 190), 2, cv2.LINE_AA)
        cv2.line(image, (480, 130), (480, 445), (90, 205, 235), 2)
        for lane, color in enumerate([(178, 214, 75), (105, 183, 250), (237, 177, 102)]):
            x = int(60 + ((frame / (90 + lane * 30)) % 1) * 840)
            y = 182 + lane * 105
            cv2.rectangle(image, (x - 22, y - 22), (x + 22, y + 22), color, -1)
            cv2.putText(image, str(lane + 1), (x - 10, y + 9), cv2.FONT_HERSHEY_SIMPLEX, .75, (25, 25, 25), 2, cv2.LINE_AA)
        cv2.putText(image, '30 FPS  /  20 s', (680, 497), cv2.FONT_HERSHEY_SIMPLEX, .65, (170, 180, 190), 1, cv2.LINE_AA)
        writer.write(image)
    writer.release()
    print(output)


if __name__ == '__main__':
    generate()
