from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template 
from google.appengine.ext.webapp import util

import os
import datetime

class Error(Exception):
  pass

class StoredImage(db.Model):
  date_start = db.DateProperty()
  date_end = db.DateProperty()
  processed_image = db.BlobProperty()

  @staticmethod
  def KeyForImage(sequence, resized=False, start_date=None, end_date=None):
    if not start_date:
      raise Error('No start date given')
    base_key = '%s_%s' % (sequence, start_date.toordinal())
    if end_date:
      base_key += '_%s' % end_date.toordinal()
    if resized:
      base_key += '_r'
    return base_key

def ImageForDay(seq, day, resized=False):
  key = StoredImage.KeyForImage(seq, resized=resized, start_date=day)
  db_value = StoredImage.get_by_key_name(key)
  if not db_value:
    db_value = StoredImage(key_name=key)
    file_name = 'processed_images/%s_%s.jpg' % (
        day.strftime('%Y%m%d'),
        seq)
    f = open(file_name)
    data = f.read()
    f.close()
    if resized:
      db_value.date_start = day
      db_value.processed_image = images.resize(data, width=800)
      db_value.put()
    else:
      db_value.processed_image = data
  return db_value.processed_image


class MainHandler(webapp.RequestHandler):
  def get(self):
    path = os.path.join(os.path.split(__file__)[0], 'processed_images/20110105_1.jpg')
    f = open(path)
    data = f.read()
    f.close()
    self.response.out.write(len(data))

class UiHandler(webapp.RequestHandler):
  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'ui.html')
    self.response.out.write(template.render(path, template_values))

class DbImageHandler(webapp.RequestHandler):
  def __ToDate(self, line):
    file_name = line[0:line.find(' ')]
    date_part = file_name[1 + file_name.find('/'):file_name.rfind('_')]
    return datetime.datetime.strptime(date_part, '%Y%m%d')

  def get(self):
    path_file = open('normalized_2.txt')
    paths = path_file.readlines()
    path_file.close()

    image_data = []
    offsets = []
    alpha = 1.0 / len(paths)
    start = int(self.request.get('start', ''))
    end = self.request.get('end')
    start_date = self.__ToDate(paths[start])
    if end:
      end = int(end)
      end_date = self.__ToDate(paths[end])
    else:
      end = start
      end_date = None

    key_name = StoredImage.KeyForImage(
      '2', resized=True, start_date=start_date, end_date=end_date)
    maybe_stored = StoredImage.get_by_key_name(key_name)

    if not maybe_stored:
      maybe_stored = StoredImage(key_name=key_name)
      alpha = 1.0 / (1 + end - start)
      for parts in paths[start:1 + end]:
        file_name, x, y = parts.strip().split(' ')
        f = open(file_name)
        data = f.read()#images.resize(f.read(), width=800)
        w = images.Image(data).width
        data = images.resize(data, width=w / 4)
        f.close()
        image_data.append(data)
        offsets.append((-int(x) / 4, -int(y) / 4))

      base_x, base_y = min(offsets)
      comp_tuples = [(data, x - base_x, y - base_y, alpha, images.TOP_LEFT)
                     for (data, (x, y)) in zip(image_data, offsets)]
      comp_data = images.composite(comp_tuples, 640, 480)
      maybe_stored.processed_image = comp_data
      maybe_stored.put()

    self.response.headers['Content-Type'] = 'image/jpg'
    self.response.out.write(maybe_stored.processed_image)


class ImageHandler(webapp.RequestHandler):
  def get(self):
    path_file = open('normalized_2.txt')
    paths = path_file.readlines()
    path_file.close()

    image_data = []
    offsets = []
    alpha = 1.0 / len(paths)
    for parts in paths:
      file_name, x, y = parts.strip().split(' ')
      f = open(file_name)
      data = f.read()#images.resize(f.read(), width=800)
      w = images.Image(data).width
      data = images.resize(data, width=w / 4)
      f.close()
      image_data.append(data)
      offsets.append((-int(x) / 4, -int(y) / 4))

    base_x, base_y = min(x[0] for x in offsets), min(x[1] for x in offsets)
    comp_tuples = [(data, x - base_x, y - base_y, alpha, images.TOP_LEFT)
                   for (data, (x, y)) in zip(image_data, offsets)]

    comp_data = images.composite(comp_tuples, 640, 480)

    self.response.headers['Content-Type'] = 'image/jpg'

    self.response.out.write(comp_data)

def main():
  application = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/ui', UiHandler),
    ('/img', ImageHandler),
    ('/db_img', DbImageHandler),
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main();
