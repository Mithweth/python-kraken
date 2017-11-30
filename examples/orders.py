#!/usr/bin/env python

import kraken
import time
import argparse

parser = argparse.ArgumentParser()
subparser = parser.add_subparsers(metavar='command')
add_parser = subparser.add_parser('add', help='add new order')
add_parser.set_defaults(command='add')
add_parser.add_argument('type')
add_parser.add_argument('volume', type=float)
add_parser.add_argument('pair')
subaddparser = add_parser.add_subparsers(metavar='ordertype')
subaddparser.add_parser('market').set_defaults(ordertype='market')
add_lim_parser = subaddparser.add_parser('limit')
add_lim_parser.set_defaults(ordertype='limit')
add_lim_parser.add_argument('price', type=float)
subparser.add_parser('list', help='list open orders').set_defaults(command='list')
del_parser = subparser.add_parser('cancel', help='cancel open order')
del_parser.set_defaults(command='cancel')
del_parser.add_argument('order')
args = parser.parse_args()

k=kraken.Kraken()
k.load_keys('keys')

if args.command == 'add':
    opts = {"price": str(args.price)} if args.ordertype == 'limit' else {}
    res = {}
    while not res:
        try:
            res = k.add_order(args.pair, args.type, args.ordertype, str(args.volume), opts)
        except kraken.HTTPError:
            time.sleep(2)
    if 'error' in res:
        print res['error'][0][1:]
    elif 'descr' in res:
        print "order %s created" % res['txid'][0]
    else:
        print res
elif args.command == 'cancel':
    res = {}
    while not res:
        try:
            res = k.cancel_order(args.order)
        except kraken.HTTPError:
            time.sleep(2)
    if 'error' in res:
        print res['error'][0][1:]
    else:
        print "order %s deleted" % args.order
elif args.command == 'list':
    res = {}
    while not res:
        try:
            res = k.open_orders()
        except kraken.HTTPError:
            time.sleep(2)
    if 'error' in res:
        print res['error'][0][1:]
    else:
        for order, data in res['open'].items():
            print "%s: %s" % (order, data['descr']['order'])

