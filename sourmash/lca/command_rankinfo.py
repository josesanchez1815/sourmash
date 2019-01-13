#! /usr/bin/env python
"""
Summarize rank-specific information from LCAs in one or more databases.
"""
from __future__ import print_function
import sys
import argparse
from collections import defaultdict

from ..logging import error, debug, set_quiet
from . import lca_utils
from ..sourmash_args import SourmashArgumentParser


def make_lca_counts(dblist):
    """
    Collect counts of all the LCAs in the list of databases.

    CTB this could usefully be converted to a generator function.
    """

    # gather all hashvalue assignments from across all the databases
    assignments = defaultdict(set)
    for lca_db in dblist:
        for hashval, idx_list in lca_db.hashval_to_idx.items():
            for idx in idx_list:
                lid = lca_db.idx_to_lid[idx]
                lineage = lca_db.lid_to_lineage[lid]
                assignments[hashval].add(lineage)

    # now convert to trees -> do LCA & counts
    counts = defaultdict(int)
    for hashval, lineages in assignments.items():

        # for each list of tuple_info [(rank, name), ...] build
        # a tree that lets us discover lowest-common-ancestor.
        debug(lineages)
        tree = lca_utils.build_tree(lineages)

        # now find either a leaf or the first node with multiple
        # children; that's our lowest-common-ancestor node.
        lca, reason = lca_utils.find_lca(tree)
        counts[lca] += 1

    return counts


def rankinfo_main(args):
    """
    rankinfo!
    """
    p = SourmashArgumentParser(prog="sourmash lca rankinfo")
    p.add_argument('db', nargs='+')
    p.add_argument('--scaled', type=float)
    p.add_argument('-q', '--quiet', action='store_true',
                   help='suppress non-error output')
    p.add_argument('-d', '--debug', action='store_true',
                   help='output debugging output')
    args = p.parse_args(args)

    if not args.db:
        error('Error! must specify at least one LCA database with --db')
        sys.exit(-1)

    set_quiet(args.quiet, args.debug)

    if args.scaled:
        args.scaled = int(args.scaled)

    # load all the databases
    dblist, ksize, scaled = lca_utils.load_databases(args.db, args.scaled)

    # count all the LCAs across these databases
    counts = make_lca_counts(dblist)

    # collect counts across all ranks
    counts_by_rank = defaultdict(int)
    for lineage, count in counts.items():
        if lineage:
            lineage_tup = lineage[-1]
            counts_by_rank[lineage_tup.rank] += count

    # output!
    total = float(sum(counts_by_rank.values()))
    for rank in lca_utils.taxlist():
        count = counts_by_rank.get(rank, 0)
        print('{}: {} ({:.1f}%)'.format(rank, count, count / total * 100.))


if __name__ == '__main__':
    sys.exit(rankinfo_main(sys.argv[1:]))
