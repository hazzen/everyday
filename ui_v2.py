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
  def __init__(self, rgb='rgb(0,0,0)', date=None):
    self.rgb = rgb
    self._SetDate(date)
    self.avg = 0
    self.min = 0
    self.max = 0
    self.img_data = []

  def __str__(self):
    return 'DayData(%s: %s avg(%s))' % (self.date, self.rgb, self.avg)

  def __repr__(self):
    return self.__str__()

  def _SetDate(self, date):
    if isinstance(date, str):
      self.date_str = date[0:8]
      self.date = datetime.datetime.strptime(self.date_str, '%Y%m%d').date()
    elif isinstance(date, datetime.date):
      self.date = date
      self.date_str = date.strftime('%Y%m%d')

  def to_json(self, parent):
    json_dict = {}
    json_dict['date'] = self.date_str
    json_dict['rgb'] = self.rgb
    json_dict['avg'] = self.avg
    json_dict['parent'] = parent
    json_dict['label'] = self.date_str
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
      if date not in day_data:
        continue
      day = day_data.get(date)
      if max[-1] == '*':
        max = max[:-1]
      if min[-1] == '*':
        min = min[:-1]
      avg, max, min = float(avg), float(max), float(min)
      avg, max, min = int(avg), int(max), int(min)
      day.SetTemps(avg=avg, min=min, max=max)

def PadDaysWithEmptys(rgbs):
  last_day = rgbs[-1]
  if last_day.date.weekday() != 5:
    rgbs.append(DayData.EmptyDay(
      last_day.date + datetime.timedelta(5 - last_day.date.weekday())))
    print rgbs[-2:]
  first_day = rgbs[0]
  if first_day.date.weekday() != 0:
    rgbs.insert(0, DayData.EmptyDay(
      first_day.date - datetime.timedelta(first_day.date.weekday())))
    print rgbs[:2]
  for index in xrange(len(rgbs) - 1, 0, -1):
    days_diff = rgbs[index].date - rgbs[index - 1].date
    if days_diff.days > 1:
      rgbs[index:index] = [
        DayData.EmptyDay(rgbs[index - 1].date + datetime.timedelta(i))
        for i in xrange(1, days_diff.days)]

def collect(iter, key_fn):
  collected = defaultdict(list)
  for item in iter:
    collected[key_fn(item)].append(item)
  return collected

def rgb_parts(val):
  return (int(x) for x in val[len('rgb('):-1].split(','))

def parts_rgb(parts):
  return 'rgb(%s)' % ','.join('%d' % x for x in parts)

def add_rgb(a, b):
  return parts_rgb(sum(x) for x in zip(rgb_parts(a), rgb_parts(b)))

def div_rgb(val, div):
  return parts_rgb(x / div for x in rgb_parts(val))


def combine_json_data(data_map, keys, parent=None):
  json_dict = {}
  json_dict['children'] = keys
  if parent:
    json_dict['parent'] = parent
  print keys
  json_dict['rgb'] = div_rgb(
    reduce(add_rgb, (data_map[key]['rgb'] for key in keys)),
    len([key for key in keys if data_map[key]['rgb'] != 'rgb(0,0,0)']))
  json_dict['avg'] = int(
    sum(data_map[key]['avg'] for key in keys) /
    len([key for key in keys if data_map[key]['avg']]))
  return json_dict

def rgbs_to_json(rgbs):
  by_week = collect(rgbs, lambda x: x.date.strftime('%U'))
  week_by_month = collect(by_week.iteritems(),
                          lambda (x, y): y[0].date.strftime('%m'))
  for value in week_by_month.itervalues():
    value.sort(key=operator.itemgetter(0))
  sorted_months = sorted(x for x in week_by_month)
  data_map = {}
  for month in sorted_months:
    month_key = '%s' % month
    data_map[month_key] = None
    week_keys = ['%s.%s' % (month, week_num)
                 for (week_num, _) in week_by_month[month]]
    for week_key, (week_num, week_data) in zip(week_keys, week_by_month[month]):
      day_keys = ['%s.%s' % (week_key, day.date.weekday())
                  for day in week_data]
      for day_key, day in zip(day_keys, week_data):
        data_map[day_key] = day.to_json(week_key)
      week_data = combine_json_data(data_map, day_keys, month_key)
      week_data['label'] = 'Week %s' % week_num
      data_map[week_key] = week_data
      
    month_data = combine_json_data(data_map, week_keys, '*')
    month_data['label'] = datetime.datetime.strptime(month, '%m').strftime('%b')
    data_map[month_key] = month_data
  data_map['*'] = combine_json_data(data_map, sorted_months)
  return data_map

class HtmlPrinter:
  def __init__(self, **options):
    self.options = options

  def _Header(self, rgbs):
    return '''
  <head>
		<link type="text/css" href="static/app.css" rel="stylesheet" />	
    <link href='http://fonts.googleapis.com/css?family=Droid+Sans:regular,bold&v1' rel='stylesheet' type='text/css'>
    <script type="text/javascript" src="static/jquery-1.5.2.js"></script>
    <script type="text/javascript" src="static/base.js"></script>
    <script type="text/javascript" src="static/ui_v2.js"></script>
    <script type="text/javascript">
      var state = 0;
      window.onload = function() {{
        var rgbs_json = {rgbs_json};
        var maker = new GraphMaker(rgbs_json);
        $('body').append(maker.graphForKey('*'));
      }};
    </script>
  </head>\n'''.format(rgbs_json=rgbs_to_json(rgbs))

  def PrintHtml(self, rgbs, out_file=sys.stdout):
    out_file.write(self._Header(rgbs))

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
