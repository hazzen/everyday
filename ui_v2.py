#! /usr/bin/env python2.7

import argparse
import datetime
import fileinput
import glob
import operator
import os.path
import shlex
import subprocess
import sys
from collections import defaultdict

def get_parser():
  parser = argparse.ArgumentParser(
      description='Convert a sequence of images into a visual barcode.')
  parser.add_argument('--offset_file', dest='offset_file')
  parser.add_argument('--weather_file',
                      dest='weather_file',
                      default='weather_data.txt')
  parser.add_argument('--weather_station',
                      dest='weather_station',
                      default='998011')
  parser.add_argument('--html_output', dest='html_output', default='')
  return parser

def run_command(cmd):
  return subprocess.check_output(shlex.split(cmd))

class ImgData:
  def __init__(self, filename='', xoff=0, yoff=0):
    self.filename = filename
    self.xoff = xoff
    self.yoff = yoff

  def to_json(self):
    return {'name': self.filename, 'xoff': self.xoff, 'yoff': self.yoff}

class DayData:
  def __init__(self, rgb='rgb(255, 255, 255)', date=None):
    self.rgb = rgb
    self._SetDate(date)
    self.avg = 0
    self.min = 0
    self.max = 0
    self.img_data = []

  def _SetDate(self, date):
    if isinstance(date, str):
      self.date_str = date[0:8]
      self.date = datetime.datetime.strptime(self.date_str, '%Y%m%d').date()
    elif isinstance(date, datetime.date):
      self.date = date
      self.date_str = date.strftime('%Y%m%d')

  def to_json(self):
    json_dict = {}
    json_dict['date'] = self.date_str
    json_dict['rgb'] = self.rgb
    json_dict['avg'] = self.avg
    img_json = [img.to_json() for img in self.img_data]
    if img_json:
      json_dict['imgs'] = img_json
    return json_dict

  @staticmethod
  def EmptyDay(date):
    empty = DayData()
    empty._SetDate(date)
    return empty

  def SetTemps(self, avg=None, max=None, min=None):
    if avg:
      self.avg = avg
    if max:
      self.max = max
    if min:
      self.min = min

  def AddImgData(self, img_data):
    self.img_data.append(img_data)


def FillTempsForDayDatas(rgbs, data_file, station):
  day_data = dict((x.date_str, x) for x in rgbs)
  for line in fileinput.input(data_file):
    if line.startswith(station):
      parts = line.split()
      date, avg, max, min = parts[2], parts[3], parts[17], parts[18]
      day = day_data.get(date)
      if not day:
        continue
      if max[-1] == '*':
        max = max[:-1]
      if min[-1] == '*':
        min = min[:-1]
      avg, max, min = float(avg), float(max), float(min)
      day.SetTemps(avg=avg, min=min, max=max)

def PadDaysWithEmptys(rgbs):
  for index in xrange(len(rgbs) - 1, 0, -1):
    days_diff = rgbs[index].date - rgbs[index - 1].date
    if days_diff.days > 1:
      rgbs[index:index] = [
        DayData.EmptyDay(rgbs[index].date + datetime.timedelta(i))
        for i in xrange(1, days_diff.days)]

def collect(iter, key_fn):
  collected = defaultdict(list)
  for item in iter:
    collected[key_fn(item)].append(item)
  return collected


def rgbs_to_json(rgbs):
  by_week = collect(rgbs, lambda x: x.date.strftime('%U'))
  week_by_month = collect(by_week.iteritems(),
                          lambda (x, y): y[0].date.strftime('%m'))
  for value in week_by_month.itervalues():
    value.sort(key=operator.itemgetter(0))
  sorted_months = sorted(x for x in week_by_month)
  json = []
  for month in sorted_months:
    month_json = []
    for _, week in week_by_month[month]:
      print week
      month_json.append([day.to_json() for day in week])
    json.append(month_json)
  print json

class HtmlPrinter:
  def __init__(self, **options):
    self.options = options

  def _Header(self):
    return '''
  <head>
		<link type="text/css" href="static/app.css" rel="stylesheet" />	
    <link href='http://fonts.googleapis.com/css?family=Droid+Sans:regular,bold&v1' rel='stylesheet' type='text/css'>
    <script type="text/javascript" src="static/jquery-1.5.2.js"></script>
    <script type="text/javascript">
      var state = 0;
      window.onload = function() {
        $('.hover').mouseover(function(e) {
          var self = $(this);
          var filename = self.attr('filename');
          var xoff = self.attr('xoff');
          var yoff = self.attr('yoff');
          var imgElem = $('#day-img');
          imgElem.attr('src', filename);
          imgElem.css({'left': 700 - parseInt(xoff) / 4, 'top': 100 - parseInt(yoff) / 4});
        });
        $('.bargraph').click(function() {
          ++state;
          state = state % 3;
          var eachFunc = function() {
            var self = $(this);
            var heightElem = self.children()[state % self.children().length];
            var newHeight = $.trim($(heightElem).text()) + '%';
            $(self.children()[0]).animate({height: newHeight}, 1000);
          };
          $(this).children('.bar').each(eachFunc);
          var labels = ['Average', 'Maximum', 'Minimum'];
          $(this).children('.title').text(labels[state % 3]);
        });
        $('.bargraph').mousemove(function(e) {
          var self = $(this);
          var topOffset = self.offset().top;
          var mouseY = 100.0 * (e.pageY - topOffset) / self.height();
          if (mouseY > 100) {
            mouseY = 100;
          } else if (mouseY < 0) {
            mouseY = 0;
          }
          var newLabel = 100 - mouseY;
          var newPosition = mouseY / 100 * self.height();
          self.find('.guide-line').css('top', newPosition + 'px');
          var label = self.find('.guide-label');
          label.html(Math.round(newLabel) + '<span class="small">&deg;F</span>');
        });
      };
    </script>
  </head>'''

  def _SingleBar(self, day_data, print_label):
    label = ''
    if print_label:
      label = '<span class="label">%s</span>' % day_data.date.strftime('%Y / %m / %d')
    extra_data = ''
    extra_classes = ''
    if hasattr(day_data, 'filename'):
      extra_data = 'filename="%s" xoff="%s" yoff="%s"' % (
        day_data.filename, day_data.xoff, day_data.yoff)
      extra_classes = ' hover'
    return '''
    <span class="bar{extra_classes}" {extra_data}>
      <span class="value" style="height: {height}%; background-color: {rgb}">
        {height}
      </span>
      <span class="tick" style="height: {max}%;">
        {max}
      </span>
      <span class="tick" style="height: {min}%;">
        {min}
      </span>
      {label}
    </span>'''.format(height=day_data.avg,
                      rgb=day_data.rgb,
                      max=day_data.max,
                      min=day_data.min,
                      extra_data=extra_data,
                      extra_classes=extra_classes,
                      label=label)

  def PrintHtml(self, rgbs, out_file=sys.stdout):
    out_file.write(self._Header())
    out_file.write('<img id="day-img" />')
    out_file.write('<div class="bargraph">')
    out_file.write('<div class="title">Average</div>')
    out_file.write('<div class="guide"><div class="guide-line"></div>')
    out_file.write('<div class="guide-label"></div></div>')
    for index, day in enumerate(rgbs):
      out_file.write(self._SingleBar(day_data=day, print_label=index % 15 == 0))
      last_day = day.date
    out_file.write('</span>')

def img_to_date_str(img_file_name):
  date_str, _ = os.path.splitext(os.path.basename(img_file_name))
  return date_str[0:8]

def main(argv):
  args = get_parser().parse_args(argv[1:])

  rgbs = []
  files = []
  for line in fileinput.input('%s_1.txt' % args.offset_file):
    file_name, xoff, yoff = line.strip().split()
    cmd = 'convert %s -scale 1x1\! -format "%%[pixel:u]" info:-' % file_name
    rgb = run_command(cmd).strip()
    date_str = img_to_date_str(file_name)
    day_data = DayData(date=date_str, rgb=rgb)
    day_data.AddImgData(ImgData(filename=file_name, xoff=xoff, yoff=yoff))
    rgbs.append(day_data)
  for line, day_data in zip(fileinput.input('%s_2.txt' % args.offset_file),
                            rgbs):
    file_name, xoff, yoff = line.strip().split()
    date_str = img_to_date_str(file_name)
    if date_str != day_data.date_str:
      raise Exception(
        'Mismatched day data: %s vs %s' % (date_str, day_data.date_str))
    day_data.AddImgData(ImgData(filename=file_name, xoff=xoff, yoff=yoff))
  rgbs.sort(key=operator.attrgetter('date'))
  rgbs_to_json(rgbs)
  FillTempsForDayDatas(rgbs,
                       data_file=args.weather_file,
                       station=args.weather_station)

  if len(rgbs):
    print 'Got %d rgb values, generating composite...' % len(rgbs)
    if args.html_output:
      PadDaysWithEmptys(rgbs)
      with open(args.html_output, 'w') as out_file:
        printer = HtmlPrinter()
        printer.PrintHtml(rgbs, out_file=out_file)

if __name__ == '__main__':
  main(sys.argv)
