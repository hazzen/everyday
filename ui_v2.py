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
  parser.add_argument('--html_output', dest='html_output')
  parser.add_argument('--composite_image_dir', dest='composite_dir')
  return parser

def run_command(cmd):
  return subprocess.check_output(shlex.split(cmd))

class ImgData:
  def __init__(self, filename='', xoff=0, yoff=0):
    self.filename = filename
    self.xoff = int(xoff)
    self.yoff = int(yoff)

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
    month_key = 'm%s' % month
    data_map[month_key] = None
    week_keys = ['%sw%s' % (month_key, week_num)
                 for (week_num, _) in week_by_month[month]]
    for week_key, (week_num, week_data) in zip(week_keys, week_by_month[month]):
      day_keys = ['%sd%s' % (week_key, day.date.weekday())
                  for day in week_data]
      for day_key, day in zip(day_keys, week_data):
        data_map[day_key] = day.to_json(week_key)
      week_data = combine_json_data(data_map, day_keys, month_key)
      week_data['label'] = 'Week %s' % week_num
      data_map[week_key] = week_data

    month_data = combine_json_data(data_map, week_keys, 'r')
    month_data['label'] = datetime.datetime.strptime(month, '%m').strftime('%b')
    data_map[month_key] = month_data
  data_map['r'] = combine_json_data(data_map,
                                    ['m%s' % m for m in sorted_months])
  return data_map


def generate_composite(rgbs_json, key, data, composite_dir, max_xoffs, max_yoffs):
  imgs = []
  explore = [data]
  while explore:
    data = explore.pop()
    data_imgs = data.get('imgs')
    if data_imgs:
      imgs.append(data_imgs)
    else:
      children = data.get('children', [])
      for child in children:
        explore.append(rgbs_json[child])

  cmds = ['convert'] * 2

  for img in imgs:
    for index, sub_img in enumerate(img):
      cmd_part = ' \( %s -distort SRT "0,0 1,1 0 %d,%d" \)' % (
        sub_img['name'],
        (max_xoffs[index] - sub_img['xoff']) / 4,
        (max_yoffs[index] - sub_img['yoff']) / 4)
      cmds[index] = cmds[index] + cmd_part
  for index, cmd in enumerate(cmds):
    cmd = '%s -average %s/%d%s.jpg' % (
      cmd,
      composite_dir,
      index,
      key)
    run_command(cmd)

class HtmlPrinter:
  def __init__(self, **options):
    self.options = options

  def _Header(self, rgbs_json):
    return '''
  <head>
    <link type="text/css" href="static/app.css" rel="stylesheet" />
    <link href='http://fonts.googleapis.com/css?family=Droid+Sans:regular,bold&v1' rel='stylesheet' type='text/css'>
    <script type="text/javascript" src="static/jquery-1.6.2.min.js"></script>
    <script type="text/javascript" src="static/base.js"></script>
    <script type="text/javascript" src="static/ui_v2.js"></script>
    <script type="text/javascript">
      var state = 0;
      window.onload = function() {{
        var rgbs_json = {rgbs_json};
        var maker = new GraphMaker(rgbs_json);
        $('#imgs').append($('<div><img id="img1" src="composites/1r.jpg"/></div>'));
        $('#imgs').append($('<div><img id="img0" src="composites/0r.jpg"/></div>'));
        $('#content').append(maker.graphForKey('r'));
        $('#content').append(maker.makeGuideBars());
        maker.resizePage();
        initPage();
      }};
    </script>
    <script type="text/javascript">
      var _gaq = _gaq || [];
      _gaq.push(['_setAccount', 'UA-24357809-1']);
      _gaq.push(['_trackPageview']);

      (function() {{
        var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
        ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
      }})();
    </script>
  </head>\n'''.format(rgbs_json=rgbs_json)

  def _Body(self, rgbs_json):
    return '''
  <div id="button-strip">
    <div class="button" id="about-button">about</div>
    <div class="button">
      <a href='https://github.com/hazzen/everyday'><span></span>code</a>
    </div>
  </div>
  <div id="about">
    <span class="content">
    <p>
    At some point last year, a friend convinced me that I should make it a
    goal to launch something, outside of work, before the end of the year.
    I had a few projects I hacked on in my spare time - some video game
    prototypes, a few that I could even play (though not, quite, enjoy). I
    thought it would be easy.
    </p>
    <p>
    I failed miserably.
    </p>
    <p>
    I decided, at the end of the year, that I would do better in the next. I
    would mount a spare android device in the window of my office. I would
    write an android app to take a photo at preset times and upload the results
    to S3, and I would do it during the two semi-vacation weeks I had for the
    holidays. I was thinking big.
    </p>
    <p>
    I failed.
    </p>
    <p>
    But I did start taking a photo, each day, as I went to lunch. The photo
    collection grew without me having a clear idea of what to do with it, other
    than "something on the internet". I played around with a lot of ideas,
    some of which you can find skeletons of in the
    <a href='https://github.com/hazzen/everyday'>git repo</a>. I threw a lot
    of it out. I didn't like the UI; hosting all the images wasn't feasible;
    it wasn't obvious what it did. But I kept at it.
    </p>
    <p>
    I made something.
    </p>
    <p>
    And here it is. Six months of photos, taken every day at lunch that I was
    in the office and remembered. Which was most days, but I wasn't entirely
    dilligent. Most photos were taken around 1230; the sound of the camera on
    the cell phone became a lunch bell for my coworkers. I've matched it up to
    some temperature data, which probably isn't for the office but seemed close
    enough. SF weather is variable enough that it is probably +/- 5 degrees
    off. And all the photos are automatically color corrected, so the color of
    the bars, taken from the average color of each photo, isn't necessarily
    correct. But, hey. I made something.
    </p>
    <p>
    And here it is.
    </p>
    </span>
  </div>
  <div id="imgs"></div>
  <div id="content"></div>
  <div id="footer">
    <em>everyday</em>: a project over 6 months by mikey.
    <br><br>
    find me on twitter @hazzen (although it mostly concerns banalities of my
    life). contact me at mrlevine using gmail.
    <br><br>
    verified to work in recent versions of chrome, safari, and firefox.
    reportedly looks ugly in ie. still attempting to find an opera user.
  </div>\n'''

  def PrintHtml(self, rgbs_json, out_file=sys.stdout):
    out_file.write(self._Header(rgbs_json))
    out_file.write(self._Body(rgbs_json))

def strip_img_data_from_json(rgbs_json):
  for v in rgbs_json.itervalues():
    v.pop('imgs', '')

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
    PadDaysWithEmptys(rgbs)
    rgbs_json = rgbs_to_json(rgbs)
    if args.composite_dir:
      num_done, num_to_do = 0, sum(1 for x in rgbs_json.itervalues()
                                   if x.get('children'))
      imgs = ([img.img_data[0], img.img_data[1]] for img in rgbs
               if img.img_data)
      a_imgs, b_imgs = zip(*imgs)
      max_xoffs = [max(img.xoff for img in a_imgs),
                   max(img.xoff for img in b_imgs)]
      max_yoffs = [max(img.yoff for img in a_imgs),
                   max(img.yoff for img in b_imgs)]
      print max_xoffs, max_yoffs
      for key, data in rgbs_json.iteritems():
        progress = num_done * 40 / num_to_do
        prog_str = 'Converting [%s%s] (%d / %d)' % (
          '=' * progress, ' ' * (40 - progress), num_done, num_to_do)
        print prog_str, '\r',
        sys.stdout.flush()
        if data.get('children'):
          generate_composite(rgbs_json, key, data, args.composite_dir,
                             max_xoffs, max_yoffs)
          num_done += 1
      print 'Done! %d composites made' % num_done
    if args.html_output:
      strip_img_data_from_json(rgbs_json)
      with open(args.html_output, 'w') as out_file:
        printer = HtmlPrinter()
        printer.PrintHtml(rgbs_json, out_file=out_file)

if __name__ == '__main__':
  main(sys.argv)
