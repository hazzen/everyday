#! /usr/bin/env python2.7

import argparse
import glob
import shlex
import subprocess
import sys

def get_parser():
  parser = argparse.ArgumentParser(
      description='Convert a sequence of images into a visual barcode.')
  parser.add_argument('--file_glob', dest='file_glob')
  parser.add_argument('--output', dest='output', default='barcode.png')
  parser.add_argument('--height', dest='height', default='300')
  parser.add_argument('--line_width', dest='line_width', default='3')
  return parser

def run_command(cmd):
  return subprocess.check_output(shlex.split(cmd))

def make_composite(rgbs, output, height, line_width):
  create_cmd = 'convert -size {width}x{height} xc:black {file_name}'.format(
      width=line_width * len(rgbs),
      height=height,
      file_name=output)
  run_command(create_cmd)
  for index, rgb in enumerate(rgbs):
    cmd = ('mogrify -stroke {rgb} -strokewidth {line_width} ' +
           ' -draw "line {x},0 {x},{height}"' +
           ' {file_name}').format(
        rgb=rgb,
        height=height,
        file_name=output,
        x=line_width * index + line_width / 2,
        line_width=line_width)
    run_command(cmd)

def main(argv):
  args = get_parser().parse_args(argv[1:])

  rgbs = []
  for file in glob.iglob(args.file_glob):
    cmd = 'convert %s -scale 1x1\! -format "%%[pixel:u]" info:-' % file
    rgb = run_command(cmd)
    rgbs.append(rgb)

  if len(rgbs):
    print 'Got %d rgb values, generating composite...' % len(rgbs)
    make_composite(rgbs, output=args.output, height=int(args.height), line_width=int(args.line_width))


if __name__ == '__main__':
  main(sys.argv)
