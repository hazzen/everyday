#! /usr/bin/env python2.7

import argparse
import fileinput
import glob
import shlex
import subprocess
import sys
import os.path

def get_parser():
  parser = argparse.ArgumentParser(
      description='Convert a sequence of images into a visual barcode.')
  parser.add_argument('--file_glob', dest='file_glob')
  parser.add_argument('--output', dest='output', default='barcode.png')
  parser.add_argument('--height', dest='height', default='300')
  parser.add_argument('--line_width', dest='line_width', default='3')
  parser.add_argument('--weather_file',
                      dest='weather_file',
                      default='weather_data.txt')
  parser.add_argument('--weather_station',
                      dest='weather_station',
                      default='998011')
  return parser

def run_command(cmd):
  return subprocess.check_output(shlex.split(cmd))

def make_composite(rgbs, output, height, line_width):
  create_cmd = 'convert -size {width}x{height} xc:black {file_name}'.format(
      width=line_width * len(rgbs),
      height=height,
      file_name=output)
  run_command(create_cmd)
  for index, dict in enumerate(rgbs):
    cmd = ('mogrify -stroke {rgb} -strokewidth {line_width} ' +
           ' -draw "line {x},0 {x},{height}"' +
           ' {file_name}').format(
        rgb=dict['rgbs'],
        height=height,
        file_name=output,
        x=line_width * index + line_width / 2,
        line_width=line_width)
    run_command(cmd)

def print_weather_html(rgbs, data, station):
  day_data = dict((os.path.basename(x['file'])[:8], x) for x in rgbs)
  print '''<html><head><style type="text/css">
    /* based on a list apart article: http://www.alistapart.com/articles/accessibledatavisualization/ */
    * { 
      margin: 0; 
      padding: 0; 
      list-style-type: none;
    }
    .bargraph { 
      float: left; 
    }
    .bargraph .bar { 
      width: 8px; 
      height: 200px; 
	    position: relative;
      float: left; 
    }
    .bargraph .bar .value { 
      display: block; 
      position: absolute; 
      bottom: 0; 
      left: 0; 
      width: 100%; 
      height: 0; 
      background: #AAA;
      overflow: hidden; 
      text-indent: -9999px;
    }
  </style></head><body>
  '''
  print '<span class="bargraph">'
  for line in fileinput.input(data):
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
      print '''
  <span class="bar"><span class="value" style="height: {height}%; background-color: {rgb}">
    {height}
  </span></span>'''.format(height=int(max),
                    rgb=day['rgbs'])
  print '</span>'

def main(argv):
  args = get_parser().parse_args(argv[1:])

  rgbs = []
  for file in glob.iglob(args.file_glob):
    cmd = 'convert %s -scale 1x1\! -format "%%[pixel:u]" info:-' % file
    rgb = run_command(cmd).strip()
    rgbs.append({'file': file, 'rgbs': rgb})

  if len(rgbs):
    print 'Got %d rgb values, generating composite...' % len(rgbs)
    make_composite(rgbs, output=args.output, height=int(args.height), line_width=int(args.line_width))
    print_weather_html(rgbs, data=args.weather_file, station=args.weather_station)


if __name__ == '__main__':
  main(sys.argv)
