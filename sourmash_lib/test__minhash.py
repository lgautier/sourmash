# This file is part of sourmash, https://github.com/dib-lab/sourmash/, and is
# Copyright (C) 2016, The Regents of the University of California.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
#     * Neither the name of the Michigan State University nor the names
#       of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written
#       permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Contact: titus@idyll.org
# pylint: disable=missing-docstring,protected-access

from __future__ import print_function
from __future__ import absolute_import, unicode_literals

from ._minhash import MinHash, hash_murmur

# add:
# * get default params from Python
# * keyword args for minhash constructor
# * trap error from handing protein/non-DNA to a DNA MH
# * fail on untagged/unloaded countgraph
# * nan on empty minhash
# * define equals

def test_basic_dna(track_abundance):
    # verify that MHs of size 1 stay size 1, & act properly as bottom sketches.
    mh = MinHash(1, 4, track_abundance=track_abundance)
    mh.add_sequence('ATGC')
    a = mh.get_mins()

    mh.add_sequence('GCAT')             # this will not get added; hash > ATGC
    b = mh.get_mins()

    print(a, b)
    assert a == b
    assert len(b) == 1


def test_protein(track_abundance):
    # verify that we can hash protein/aa sequences
    mh = MinHash(10, 6, True, track_abundance=track_abundance)
    mh.add_protein('AGYYG')

    assert len(mh.get_mins()) == 4


def test_protein_short(track_abundance):
    # verify that we can hash protein/aa sequences
    mh = MinHash(10, 9, True, track_abundance=track_abundance)
    mh.add_protein('AG')

    assert len(mh.get_mins()) == 0, mh.get_mins()


def test_basic_dna_bad(track_abundance):
    # test behavior on bad DNA
    mh = MinHash(1, 4, track_abundance=track_abundance)
    try:
        mh.add_sequence('ATGR')
        assert 0, "should fail on invalid DNA sequence"
    except ValueError:
        pass


def test_basic_dna_bad_2(track_abundance):
    # test behavior on bad DNA
    mh = MinHash(1, 6, track_abundance=track_abundance)
    try:
        mh.add_protein('YYYY')
        assert 0, "should fail => this is a DNA MinHash"
    except ValueError:
        pass


def test_basic_dna_bad_force(track_abundance):
    # test behavior on bad DNA
    mh = MinHash(1, 4, track_abundance=track_abundance)
    assert len(mh.get_mins()) == 0
    mh.add_sequence('ATGR', True)
    assert len(mh.get_mins()) == 1
    mh.add_sequence('ATGN', True)         # R --> N w/force
    assert len(mh.get_mins()) == 1
    mh.add_sequence('NCAT', True)         # reverse complement of N -> N
    assert len(mh.get_mins()) == 1


def test_compare_1(track_abundance):
    a = MinHash(20, 10, track_abundance=track_abundance)
    b = MinHash(20, 10, track_abundance=track_abundance)

    a.add_sequence('TGCCGCCCAGCACCGGGTGACTAGGTTGAGCCATGATTAACCTGCAATGA')
    b.add_sequence('TGCCGCCCAGCACCGGGTGACTAGGTTGAGCCATGATTAACCTGCAATGA')

    assert a.compare(b) == 1.0
    assert b.compare(b) == 1.0
    assert b.compare(a) == 1.0
    assert a.compare(a) == 1.0

    # add same sequence again
    b.add_sequence('TGCCGCCCAGCACCGGGTGACTAGGTTGAGCCATGATTAACCTGCAATGA')
    assert a.compare(b) == 1.0
    assert b.compare(b) == 1.0
    assert b.compare(a) == 1.0
    assert a.compare(a) == 1.0


    b.add_sequence('GATTGGTGCACACTTAACTGGGTGCCGCGCTGGTGCTGATCCATGAAGTT')
    x = a.compare(b)
    assert x >= 0.3, x

    x = b.compare(a)
    assert x >= 0.3, x
    assert a.compare(a) == 1.0
    assert b.compare(b) == 1.0


def test_mh_copy(track_abundance):
    a = MinHash(20, 10, track_abundance=track_abundance)

    a.add_sequence('TGCCGCCCAGCACCGGGTGACTAGGTTGAGCCATGATTAACCTGCAATGA')
    b = a.__copy__()
    assert b.compare(a) == 1.0


def test_mh_len(track_abundance):
    a = MinHash(20, 10, track_abundance=track_abundance)

    assert len(a) == 20
    a.add_sequence('TGCCGCCCAGCACCGGGTGACTAGGTTGAGCCATGATTAACCTGCAATGA')
    assert len(a) == 20


def test_mh_len(track_abundance):
    a = MinHash(20, 10, track_abundance=track_abundance)
    for i in range(0, 40, 2):
        a.add_hash(i)

    assert a.get_mins() == list(range(0, 40, 2))


def test_mh_unsigned_long_long(track_abundance):
    a = MinHash(20, 10, track_abundance=track_abundance)
    a.add_hash(9227159859419181011)        # too big for a C long int.
    assert 9227159859419181011 in a.get_mins()


def test_mh_count_common(track_abundance):
    a = MinHash(20, 10, track_abundance=track_abundance)
    for i in range(0, 40, 2):
        a.add_hash(i)

    b = MinHash(20, 10, track_abundance=track_abundance)
    for i in range(0, 80, 4):
        b.add_hash(i)

    assert a.count_common(b) == 10
    assert b.count_common(a) == 10


def test_mh_count_common_diff_protein(track_abundance):
    a = MinHash(20, 5, False, track_abundance=track_abundance)
    b = MinHash(20, 5, True, track_abundance=track_abundance)

    try:
        a.count_common(b)
        assert 0, "count_common should fail with DNA vs protein"
    except ValueError:
        pass


def test_mh_count_common_diff_ksize(track_abundance):
    a = MinHash(20, 5, track_abundance=track_abundance)
    b = MinHash(20, 6, track_abundance=track_abundance)

    try:
        a.count_common(b)
        assert 0, "count_common should fail with different ksize"
    except ValueError:
        pass


def test_mh_asymmetric(track_abundance):
    a = MinHash(20, 10, track_abundance=track_abundance)
    for i in range(0, 40, 2):
        a.add_hash(i)

    b = MinHash(10, 10, track_abundance=track_abundance)                   # different size: 10
    for i in range(0, 80, 4):
        b.add_hash(i)

    assert a.count_common(b) == 10
    assert b.count_common(a) == 10

    assert a.compare(b) == 0.5
    assert b.compare(a) == 1.0


def test_mh_merge(track_abundance):
    # test merging two identically configured minhashes
    a = MinHash(20, 10, track_abundance=track_abundance)
    for i in range(0, 40, 2):
        a.add_hash(i)

    b = MinHash(20, 10, track_abundance=track_abundance)
    for i in range(0, 80, 4):
        b.add_hash(i)

    c = a.merge(b)
    d = b.merge(a)

    assert len(c) == len(d)
    assert c.get_mins() == d.get_mins()
    assert c.compare(d) == 1.0
    assert d.compare(c) == 1.0




def test_mh_asymmetric_merge(track_abundance):
    # test merging two asymmetric (different size) MHs
    a = MinHash(20, 10, track_abundance=track_abundance)
    for i in range(0, 40, 2):
        a.add_hash(i)

    b = MinHash(10, 10, track_abundance=track_abundance)                   # different size: 10
    for i in range(0, 80, 4):
        b.add_hash(i)

    c = a.merge(b)
    d = b.merge(a)

    assert len(a) == 20
    assert len(b) == 10
    assert len(c) == len(a)
    assert len(d) == len(b)

    assert d.compare(a) == 1.0
    assert c.compare(b) == 0.5


def test_mh_inplace_concat_asymmetric(track_abundance):
    # test merging two asymmetric (different size) MHs
    a = MinHash(20, 10, track_abundance=track_abundance)
    for i in range(0, 40, 2):
        a.add_hash(i)

    b = MinHash(10, 10, track_abundance=track_abundance)                   # different size: 10
    for i in range(0, 80, 4):
        b.add_hash(i)

    c = a.__copy__()
    c += b

    d = b.__copy__()
    d += a

    assert len(a) == 20
    assert len(b) == 10
    assert len(c) == len(a)
    assert len(d) == len(b)

    assert d.compare(a) == 1.0
    assert c.compare(b) == 0.5


def test_mh_inplace_concat(track_abundance):
    # test merging two identically configured minhashes
    a = MinHash(20, 10, track_abundance=track_abundance)
    for i in range(0, 40, 2):
        a.add_hash(i)

    b = MinHash(20, 10, track_abundance=track_abundance)
    for i in range(0, 80, 4):
        b.add_hash(i)

    c = a.__copy__()
    c += b
    d = b.__copy__()
    d += a

    assert len(c) == len(d)
    assert c.get_mins() == d.get_mins()
    assert c.compare(d) == 1.0
    assert d.compare(c) == 1.0

def test_mh_merge_diff_protein(track_abundance):
    a = MinHash(20, 5, False, track_abundance=track_abundance)
    b = MinHash(20, 5, True, track_abundance=track_abundance)

    try:
        a.merge(b)
        assert 0, "merge should fail with DNA vs protein"
    except ValueError:
        pass


def test_mh_merge_diff_ksize(track_abundance):
    a = MinHash(20, 5, track_abundance=track_abundance)
    b = MinHash(20, 6, track_abundance=track_abundance)

    try:
        a.merge(b)
        assert 0, "merge should fail with different ksize"
    except ValueError:
        pass


def test_mh_compare_diff_protein(track_abundance):
    a = MinHash(20, 5, False, track_abundance=track_abundance)
    b = MinHash(20, 5, True, track_abundance=track_abundance)

    try:
        a.compare(b)
        assert 0, "compare should fail with DNA vs protein"
    except ValueError:
        pass


def test_mh_compare_diff_ksize(track_abundance):
    a = MinHash(20, 5, track_abundance=track_abundance)
    b = MinHash(20, 6, track_abundance=track_abundance)

    try:
        a.compare(b)
        assert 0, "compare should fail with different ksize"
    except ValueError:
        pass


def test_mh_concat_diff_protein(track_abundance):
    a = MinHash(20, 5, False, track_abundance=track_abundance)
    b = MinHash(20, 5, True, track_abundance=track_abundance)

    try:
        a += b
        assert 0, "concat should fail with DNA vs protein"
    except ValueError:
        pass


def test_mh_concat_diff_ksize(track_abundance):
    a = MinHash(20, 5, track_abundance=track_abundance)
    b = MinHash(20, 6, track_abundance=track_abundance)

    try:
        a += b
        assert 0, "concat should fail with different ksize"
    except ValueError:
        pass


def test_short_sequence(track_abundance):
    a = MinHash(20, 5, track_abundance=track_abundance)
    a.add_sequence('GGGG')
    # adding a short sequence should fail silently
    assert len(a.get_mins()) == 0


def test_murmur():
    x = hash_murmur("ACG")
    assert x == 1731421407650554201

    try:
        x = hash_murmur()
        assert 0, "hash_murmur requires an argument"
    except TypeError:
        pass


def test_abundance_simple():
    a = MinHash(20, 5, False, track_abundance=True)

    a.add_sequence('AAAAA')
    assert a.get_mins() == [2110480117637990133]
    assert a.get_mins(with_abundance=True) == {2110480117637990133: 1}

    a.add_sequence('AAAAA')
    assert a.get_mins() == [2110480117637990133]
    assert a.get_mins(with_abundance=True) == {2110480117637990133: 2}


def test_abundance_simple_2():
    a = MinHash(20, 5, False, track_abundance=True)
    b = MinHash(20, 5, False, track_abundance=True)

    a.add_sequence('AAAAA')
    assert a.get_mins() == [2110480117637990133]
    assert a.get_mins(with_abundance=True) == {2110480117637990133: 1}

    a.add_sequence('AAAAA')
    assert a.get_mins() == [2110480117637990133]
    assert a.get_mins(with_abundance=True) == {2110480117637990133: 2}

    b.add_sequence('AAAAA')
    assert a.count_common(b) == 1


def test_abundance_count_common():
    a = MinHash(20, 5, False, track_abundance=True)
    b = MinHash(20, 5, False, track_abundance=False)

    a.add_sequence('AAAAA')
    a.add_sequence('AAAAA')
    assert a.get_mins() == [2110480117637990133]
    assert a.get_mins(with_abundance=True) == {2110480117637990133: 2}

    b.add_sequence('AAAAA')
    b.add_sequence('GGGGG')
    assert a.count_common(b) == 1
    assert a.count_common(b) == b.count_common(a)

    assert b.get_mins(with_abundance=True) == [2110480117637990133,
                                               10798773792509008305]

def test_abundance_compare():
    a = MinHash(20, 10, track_abundance=True)
    b = MinHash(20, 10, track_abundance=False)

    a.add_sequence('TGCCGCCCAGCACCGGGTGACTAGGTTGAGCCATGATTAACCTGCAATGA')
    b.add_sequence('TGCCGCCCAGCACCGGGTGACTAGGTTGAGCCATGATTAACCTGCAATGA')

    assert a.compare(b) == 1.0
    assert b.compare(b) == 1.0
    assert b.compare(a) == 1.0
    assert a.compare(a) == 1.0

    # add same sequence again
    b.add_sequence('TGCCGCCCAGCACCGGGTGACTAGGTTGAGCCATGATTAACCTGCAATGA')
    assert a.compare(b) == 1.0
    assert b.compare(b) == 1.0
    assert b.compare(a) == 1.0
    assert a.compare(a) == 1.0

    b.add_sequence('GATTGGTGCACACTTAACTGGGTGCCGCGCTGGTGCTGATCCATGAAGTT')
    x = a.compare(b)
    assert x >= 0.3, x

    x = b.compare(a)
    assert x >= 0.3, x
    assert a.compare(a) == 1.0
    assert b.compare(b) == 1.0
