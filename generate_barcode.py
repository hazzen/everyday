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

def get_parser():
  parser = argparse.ArgumentParser(
      description='Convert a sequence of images into a visual barcode.')
  parser.add_argument('--file_glob', dest='file_glob')
  parser.add_argument('--offset_file', dest='offset_file')
  parser.add_argument('--output', dest='output', default='')
  parser.add_argument('--height', dest='height', default='300')
  parser.add_argument('--line_width', dest='line_width', default='3')
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

def make_composite(rgbs, output, height, line_width):
  create_cmd = 'convert -size {width}x{height} xc:black {file_name}'.format(
      width=line_width * len(rgbs),
      height=height,
      file_name=output)
  run_command(create_cmd)
  for index, day_data in enumerate(rgbs):
    cmd = ('mogrify -stroke {rgb} -strokewidth {line_width} ' +
           ' -draw "line {x},0 {x},{height}"' +
           ' {file_name}').format(
        rgb=day_data.rgb,
        height=height,
        file_name=output,
        x=line_width * index + line_width / 2,
        line_width=line_width)
    run_command(cmd)

class DayData:
  def __init__(self, filename='', rgb='rgb(255, 255, 255)', xoff=0, yoff=0):
    self.rgb = rgb
    self.xoff = xoff
    self.yoff = yoff
    if filename:
      self.filename = filename
      self._SetDate(os.path.basename(self.filename)[:8])
    self.avg = 0
    self.min = 0
    self.max = 0

  def _SetDate(self, date):
    self.date_str = date
    year = int(date[0:4], 10)
    month = int(date[4:6], 10)
    day = int(date[6:8], 10)
    self.date = datetime.date(year, month, day)

  @staticmethod
  def EmptyDay(date):
    empty = DayData()
    empty._SetDate(date.strftime('%Y%m%d'))
    return empty

  def SetTemps(self, avg=None, max=None, min=None):
    if avg:
      self.avg = avg
    if max:
      self.max = max
    if min:
      self.min = min

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

def main(argv):
  args = get_parser().parse_args(argv[1:])

  rgbs = []
  if args.offset_file:
    files = []
    for line in fileinput.input(args.offset_file):
      file_name, xoff, yoff = line.strip().split()
      files.append((file_name, xoff, yoff))
  else:
    files = ((x, 0, 0) for x in glob.iglob(args.file_glob))
  for (file, xoff, yoff) in files:
    cmd = 'convert %s -scale 1x1\! -format "%%[pixel:u]" info:-' % file
    rgb = run_command(cmd).strip()
    rgbs.append(DayData(filename=file, rgb=rgb, xoff=xoff, yoff=yoff))
  rgbs.sort(key=operator.attrgetter('date'))
  FillTempsForDayDatas(rgbs,
                       data_file=args.weather_file,
                       station=args.weather_station)

  if len(rgbs):
    print 'Got %d rgb values, generating composite...' % len(rgbs)
    if args.output:
      make_composite(rgbs,
                     output=args.output,
                     height=int(args.height),
                     line_width=int(args.line_width))
    if args.html_output:
      PadDaysWithEmptys(rgbs)
      with open(args.html_output, 'w') as out_file:
        printer = HtmlPrinter()
        printer.PrintHtml(rgbs, out_file=out_file)

if __name__ == '__main__':
  main(sys.argv)
