# download patents from Google

import argparse
import collections
import logging
import os
import re
import traceback
from urlparse import urlparse
import sys

from lxml import html
import requests


def download_urls(url_list, output_dir):
    for url in url_list:
        filename = os.path.basename(url)
        logging.info('downloading: {}'.format(filename))
        with open(os.path.join(output_dir, filename), 'wb') as fd:
            file_obj = requests.get(url, stream=True)
            for chunk in file_obj.iter_content():
                fd.write(chunk)


def download_html(page, output_dir):
    patent_basename = os.path.basename(urlparse(page.url).path)
    html_filename = patent_basename + '.html'
    logging.info('downloading: {}'.format(html_filename))
    with open(os.path.join(output_dir, html_filename), 'wb') as fd:
        page_text = page.text
        page_text = page_text.replace('//patentimages.storage.googleapis.com/{}/'.format(patent_basename), '')
        page_text = page_text.replace('//patentimages.storage.googleapis.com/thumbnails/{}/'.format(patent_basename),
                                      'thumbnails/')
        page_text = re.sub(r'/patents/css/[^/]*/', '', page_text)
        fd.write(page_text.encode('utf8'))


def parse_command_line():
    parser = argparse.ArgumentParser(description='download patents',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--start', type=int, help='start patent id')
    parser.add_argument('--end', type=int, help='end patent id (inclusive)')
    parser.add_argument('--output_dir', type=str, help='output directory', default='./')
    parser.add_argument('--org', type=str, help='prefix of the organization publishing the patent', default='EP',
                        choices=['EP', 'US', 'WO', 'DE'])
    patent_kinds = ['A1', 'A9', 'B1', 'B2', 'C1', 'E1', 'F1', 'H', 'I1', 'I2',
                    'I3', 'I4', 'I5', 'P1', 'P1', 'P2', 'P3', 'S', 'X6', 'X7', ]
    parser.add_argument('--kind',
                        type=str,
                        dest='patent_kinds',
                        action='append',
                        help='kind of the patent (can have multiple entries: e.g. --kind A1 --kind B1)',
                        default=patent_kinds,
                        choices=patent_kinds)
    parser.add_argument('--version', action='version', version='%(prog)s 1.2')

    if len(sys.argv) == 1:
        parser.print_help()
        exit(1)

    args = parser.parse_args(sys.argv[1:])
    logging.info('args: {}'.format(args))
    return args


def download_images(tree, patent_dir):
    image_thumbnail_urls = tree.xpath('//img[@class="patent-thumbnail-image"]/@src')
    if image_thumbnail_urls:
        image_thumbnail_urls = ['http:' + u for u in image_thumbnail_urls]
        thumbnail_dir = os.path.join(patent_dir, 'thumbnails')
        if not os.path.exists(thumbnail_dir):
            os.makedirs(thumbnail_dir)
        download_urls(image_thumbnail_urls, thumbnail_dir)
        image_urls = [u.replace('thumbnails/', '') for u in image_thumbnail_urls]
        download_urls(image_urls, patent_dir)

    image_urls = tree.xpath('//img[@class="patent-full-image"]/@src')
    if image_urls:
        image_urls = ['http:' + u for u in image_urls]
        download_urls(image_urls, patent_dir)


def download_pdfs(tree, patent_dir):
    pdf_urls = tree.xpath('//a[@id="appbar-download-pdf-link"]/@href')
    if pdf_urls:
        pdf_urls = ['http:' + u for u in pdf_urls if u != '']
        download_urls(pdf_urls, patent_dir)


def download_css(tree, patent_dir):
    css_urls = tree.xpath('//link[@rel="stylesheet"]/@href')
    if css_urls:
        css_urls = ['http://www.google.com' + u for u in css_urls if u != '']
        download_urls(css_urls, patent_dir)


def process_patent(args, patent_number):

    logging.info('processing patent {}'.format(patent_number))

    patent_exists = False
    for kind in (args.patent_kinds):
        # build patent name
        patent = '{2}{0:07}{1}'.format(patent_number, kind, args.org)
        logging.info('trying kind {}'.format(kind))

        # read patent page
        page = requests.get('http://www.google.com/patents/' + patent + '?cl=de')
        if page.status_code == 200:
            logging.info('found patent {}'.format(patent))

            tree = html.fromstring(page.text)

            # create output directory
            patent_dir = os.path.join(args.output_dir, patent)
            if not os.path.exists(patent_dir):
                os.makedirs(patent_dir)

            # download patent artifacts
            download_html(page, patent_dir)
            download_images(tree, patent_dir)
            download_pdfs(tree, patent_dir)
            download_css(tree, patent_dir)

            patent_exists = True
        else:
            # continue searching for a valid patent kind
            logging.info('kind {0} not found for patent {2}{1}'.format(kind, patent_number, args.org))
            continue
    return patent_exists


def init_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')


def main():
    init_logging()
    args = parse_command_line()
    logging.info('downloading patents {} through {}'.format(args.start, args.end))
    logging.info('output directory: {}'.format(os.path.abspath(args.output_dir)))
    stats = collections.Counter()
    for patent_number in xrange(args.start, args.end + 1):
        try:
            if not process_patent(args, patent_number):
                logging.ERROR('patent number {} does not exist'.format(patent_number))
                stats.update({'error': 1})
                logging.info('stats: {}'.format(stats))
                exit(2)
            stats.update({'success': 1})
        except Exception, e:
            logging.warning('problem processing patent {}'.format(patent_number, e))
            traceback.print_exc()
            stats.update({'warning': 1})

    logging.info('stats: {}'.format(stats))


if __name__ == '__main__':
    main()
