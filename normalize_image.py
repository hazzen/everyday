import sys

from PyQt4 import QtCore
from PyQt4 import QtGui

class ImageView(QtGui.QGraphicsView):
  def __init__(self, parent=None, origPixmap=None, images=None):
    super(ImageView, self).__init__(parent)
    self.origPixmap = origPixmap
    self.images = images
    QtCore.QMetaObject.connectSlotsByName(self)

  def resizeEvent(self, event):
    self.resizeEventImpl(event.size())

  def resizeEventImpl(self, size):
    item = self.items()[0]

    pixmap = self.origPixmap
    pixmap = pixmap.scaled(
      size,
      QtCore.Qt.KeepAspectRatio,
      QtCore.Qt.SmoothTransformation)
    self.centerOn(1.0, 1.0)
    item.setPixmap(pixmap)

  def mousePressEvent(self, event):
    origSize = self.origPixmap.size()
    curSize = self.size()
    pos = event.pos()
    scaledX = int(1.0 * origSize.width() / curSize.width() * pos.x())
    scaledY = int(1.0 * origSize.height() / curSize.height() * pos.y())
    print '%s %s %s' % (self.images[0], scaledX, scaledY)
    self.nextImage()

  def setImage(self, image):
    pic = QtGui.QPixmap(image)
    self.origPixmap = pic
    self.resizeEventImpl(self.size())

  def nextImage(self):
    self.images = self.images[1:]
    if self.images:
      self.setImage(self.images[0])
    else:
      sys.exit(0)


def genImageNames(fileName):
  f = open(fileName)
  names = f.readlines()
  f.close()
  names = ['processed_images/%s' % x.strip() for x in names]
  return names

def main():
  images = genImageNames('names.txt')
  app = QtGui.QApplication(sys.argv)
  pic = QtGui.QPixmap(images[0])
  view = ImageView(origPixmap=pic, images=images[1:])
  scene = QtGui.QGraphicsScene()
  scene.addPixmap(pic)

  view.setScene(scene)
  view.show()

  sys.exit(app.exec_())

if __name__ == '__main__':
  main();
