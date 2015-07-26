import Image

im = Image.open('petscii.png')

out = Image.new("RGBA",(145,73))

for x in xrange(16):
  for y in xrange(8):
    src = im.crop( (x*8, y*8, (x+1)*8, (y+1)*8) )
    out.paste(src, (x*9+1, y*9+1, (x*9)+9, y*9+9) )

out.save('petscii_expanded.png')
