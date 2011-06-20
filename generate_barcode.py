#! /usr/bin/env python2.7

import argparse
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
  def __init__(self, filename='', rgb=''):
    self.filename = filename
    self.rgb = rgb
    if filename:
      self.date = os.path.basename(self.filename)[:8]

  def SetTemps(self, avg=None, max=None, min=None):
    if avg:
      self.avg = avg
    if max:
      self.max = max
    if min:
      self.min = min

def FillTempsForDayDatas(rgbs, data_file, station):
  day_data = dict((x.date, x) for x in rgbs)
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

class HtmlPrinter:
  def __init__(self):
    pass

  def _Header(self):
    return '''
  <head>
		<link type="text/css" href="static/app.css" rel="stylesheet" />	
    <script type="text/javascript" src="static/jquery-1.5.2.js"></script>
    <script type="text/javascript">
      window.onload = function() {
        $('.bargraph').click(function() {
          $(this).children('.bar').each(function() {
            var self = $(this);
            state = self.attr('state')
            if (!state) {
              state = '0';
            }
            var state = parseInt(state);
            state += 1;
            self.attr('state', state);
            var heightElem = self.children()[state % self.children().length];
            var newHeight = $.trim($(heightElem).text()) + '%';
            $(self.children()[0]).animate({height: newHeight}, 1000);
          });
        });
      };
    </script>
  </head>'''

  def _SingleBar(self, **format_data):
    return '''
    <span class="bar">
      <span class="value" style="height: {height}%; background-color: {rgb}">
        {height}
      </span>
      <span class="tick" style="height: {max}%; border-top: thin solid black;">
        {max}
      </span>
      <span class="tick" style="height: {min}%; border-top: thin solid black;">
        {min}
      </span>
    </span>'''.format(**format_data)

  def PrintHtml(self, rgbs, out_file=sys.stdout):
    out_file.write(self._Header())
    out_file.write('<span class="bargraph">')
    for day in rgbs:
      print day.date
      out_file.write(self._SingleBar(height=day.avg,
                                     max=day.max,
                                     min=day.min,
                                     rgb=day.rgb))
    out_file.write('</span>')

def main(argv):
  args = get_parser().parse_args(argv[1:])

  rgbs = []
  for file in glob.iglob(args.file_glob):
    cmd = 'convert %s -scale 1x1\! -format "%%[pixel:u]" info:-' % file
    rgb = run_command(cmd).strip()
    rgbs.append(DayData(filename=file, rgb=rgb))
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
      with open(args.html_output, 'w') as out_file:
        printer = HtmlPrinter()
        printer.PrintHtml(rgbs, out_file=out_file)

if __name__ == '__main__':
  main(sys.argv)
