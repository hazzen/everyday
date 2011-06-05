#! /usr/bin/env python2.7

import argparse
import os
import sys
import shutil
from collections import defaultdict

def group_by_day(names):
  grouped = defaultdict(list)
  leader = 'IMG_'
  trailer = '_'
  for name in names:
    leader_index = name.index(leader) + len(leader)
    day_part = name[leader_index : name.index(trailer, leader_index)]
    grouped[day_part].append(name)

  for k, v in grouped.iteritems():
    if len(v) != 2:
      raise ValueError('Found a key "%s" with %d items: %d' % (k, len(v), v))
  return grouped

def get_parser():
  parser = argparse.ArgumentParser(
      description='Copy img files to proper naming scheme.')
  parser.add_argument('--in_dir', dest='in_dir', default='images/')
  parser.add_argument('--out_dir', dest='out_dir', default='images/')
  return parser

def main(argv):
  images = []
  args = get_parser().parse_args(argv[1:])

  path_to_images = os.path.abspath(args.in_dir)
  path_to_out_images = os.path.abspath(args.out_dir)

  for img_file in os.listdir(path_to_images):
    images.append(img_file)
  images.sort()
  grouped = group_by_day(images)
  for day, [img_one, img_two]  in grouped.iteritems():
    shutil.copy(os.path.join(path_to_images, img_one),
                os.path.join(path_to_out_images, '%s_1.jpg' % day))
    shutil.copy(os.path.join(path_to_images, img_two),
                os.path.join(path_to_out_images, '%s_2.jpg' % day))

if __name__ == '__main__':
  main(sys.argv)
