#! /usr/bin/env python
"""
Use the MurmurHash library mmh3 and separate Python code to calculate
a MinHash signature for input DNA sequence, as a way to do an
external check on our C++ implementation.

The output of this is used in test_sourmash.py to verify our C++ code.
"""
import ctypes

__complementTranslation = { "A": "T", "C": "G", "G": "C", "T": "A", "N": "N" }
def complement(s):
    """
    Return complement of 's'.
    """
    c = "".join(__complementTranslation[n] for n in s)
    return c


def reverse(s):
    """
    Return reverse of 's'.
    """
    r = "".join(reversed(s))
    return r


def kmers(seq, k):
    for start in range(len(seq) - k + 1):
        yield seq[start:start + k]

###

K = 21

import sys, screed
import mmh3
import sourmash_lib
print('imported sourmash:', sourmash_lib, file=sys.stderr)
from sourmash_lib import MinHash
import sourmash_lib.signature

record = next(iter(screed.open(sys.argv[1])))
print('loaded', record.name, file=sys.stderr)
revcomp = reverse(complement((record.sequence)))

mh = sourmash_lib.MinHash(ksize=K, n=500, is_protein=False)

for fwd_kmer in kmers(record.sequence, K):
    rev_kmer = reverse(complement(fwd_kmer))
    if fwd_kmer < rev_kmer:
        kmer = fwd_kmer
    else:
        kmer = rev_kmer

    hash = mmh3.hash64(kmer, seed=42)[0]

    # convert to unsigned int if negative
    if hash < 0:
        hash += 2**64

    mh.add_hash(hash)

s = sourmash_lib.signature.SourmashSignature('', mh, name=record.name)
print(sourmash_lib.signature.save_signatures([s]))
