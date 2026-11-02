"""Generate an original two-page layout fixture, not a PDF extraction pipeline.
Requires existing reportlab, Pillow, and system DejaVu Sans fonts. Run: python make_fixture.py [output.pdf]
Page 2 is deliberately image-only. No network or external content is used.
"""
from io import BytesIO
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name('layout.pdf')
# Embedded fonts keep the synthetic layout stable without renderer font substitution.
pdfmetrics.registerFont(TTFont('Fixture', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('FixtureBold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
c = canvas.Canvas(str(out), pagesize=(595, 842), invariant=1)
c.setTitle('Synthetic layout recognition fixture')
c.setAuthor('Synthetic Example')
def text(x, y, lines, size=11, leading=17, bold=False):
    c.setFont('FixtureBold' if bold else 'Fixture', size)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading

text(42, 807, ['SYNTHETIC JOURNAL | layout test'], 9)
text(42, 765, ['A bounded estimator'], 24, bold=True)
text(42, 733, ['Abstract'], 13, bold=True)
text(42, 711, ['The latent state is not observed. Error decreases only if noise is independent.',
               'This synthetic page has a full-width abstract above two body columns.'])
text(42, 647, ['1. Method'], 15, bold=True)
text(42, 621, ['Read this left column first.', 'The latent state remains fixed',
              'unless an intervention changes it.', 'A 12.5% improvement occurred',
              'at 20 ms, but not at 10 ms [1].'])
text(42, 514, ['e(z) <= 0.05'], 14)
text(42, 477, ['The bound is sufficient,', 'not necessary. Continue at the',
              'top of the right column.'])
text(315, 647, ['2. Results'], 15, bold=True)
text(315, 621, ['This is the second body column.', 'Prediction does not imply causation.'])
c.rect(315, 504, 230, 67)
text(327, 541, ['Input  ->  Latent state'], 12)
text(315, 483, ['Figure 1. Prediction, not causation.'], 10)
text(315, 439, ['Table 1. Conditional error.'], 10)
for y in (423, 400, 377, 354): c.line(315, y, 545, y)
for x in (315, 480, 545): c.line(x, 354, x, 423)
text(322, 408, ['Setting'], 10); text(488, 408, ['Error'], 10)
text(322, 385, ['Independent noise'], 10); text(488, 385, ['0.04'], 10)
text(322, 362, ['Dependent noise'], 10); text(488, 362, ['0.12'], 10)
c.line(42, 115, 275, 115)
text(42, 96, ['[1] Timing excludes initialization.'], 9)
text(42, 49, ['Synthetic running footer - not body prose'], 9)
text(540, 49, ['1'], 9)
c.showPage()
# Raster text deliberately removes an extractable text layer from the appendix.
im = Image.new('RGB', (1190, 1684), 'white')
d = ImageDraw.Draw(im)
font = ImageFont.load_default(size=23)
heading = ImageFont.load_default(size=38)
d.text((84, 66), 'SYNTHETIC JOURNAL | scanned appendix', fill='black', font=font)
d.text((84, 160), 'Appendix A. Limits', fill='black', font=heading)
for y, line in enumerate([
    'This image-only page uses a single column.',
    'The latent state may change under an intervention.',
    'The bound may fail under dependent noise.',
    'The threshold is 0.05, not 0.5.',
    'Read symbols against the pixels, not an empty text extraction.',
]): d.text((84, 260 + y*56), line, fill='black', font=font)
d.line((84, 1460, 680, 1460), fill='black', width=2)
d.text((84, 1480), '[2] No observations were removed.', fill='black', font=font)
d.text((84, 1570), 'Synthetic running footer - not body prose', fill='black', font=font)
d.text((1080, 1570), '2', fill='black', font=font)
b = BytesIO(); im.save(b, format='PNG'); b.seek(0)
c.drawImage(ImageReader(b), 0, 0, width=595, height=842)
c.save()
print(out)
