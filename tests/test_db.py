#!/usr/bin/env python
#
# Author: Thamme Gowda [tg (at) isi (dot) edu] 
# Created: 7/19/20

from nlcodec.db.core import Db, MultipartDb, best_type
import numpy as np
import random
from pathlib import Path
import shutil


def test_db():
    def get_data():
        for i in range(20000):
            l = np.random.randint(4, 25)
            x = np.random.randint(0, 33000, l)
            y = np.random.randint(0, 33000, l + random.randint(0, 5))
            yield x, y

    recs = list(get_data())
    db = Db.create(recs=recs, names=['x', 'y'])
    assert len(db) == len(recs)
    for (x, y), (_id, row) in zip(recs, db):
        assert np.array_equal(row.x, x)
        assert np.array_equal(row.y, y)


def test_multipart_db():
    n_parts = 10
    total = 100_000 + (n_parts - 1)
    vocab_size = 33_000

    def get_data():
        for i in range(total):
            l = np.random.randint(4, 25)
            x = np.random.randint(0, vocab_size, l)
            y = np.random.randint(0, vocab_size, l + random.randint(0, 5))
            yield x, y

    recs = {i: r for i, r in enumerate(get_data())}

    path = Path('tmp.test.multipartdb')
    try:
        db = MultipartDb.create(path=path, recs=recs.items(), has_id=True,
                                names=['x', 'y'], part_size=total // n_parts,
                                overwrite=True)
        assert len(db) == len(recs)
        for id1, row in db:
            x,y = recs[id1]
            assert np.array_equal(row.x, x), f'{id1} :: {row.x} == {x}'
            assert np.array_equal(row.y, y), f'{id1} :: {row.y} == {y}'
    finally:
        shutil.rmtree(path)
        pass


def test_large_db():
    n_parts = 20
    total = 1_000_000  # lines  can go upto 500M
    vocab_size = 64_000

    def get_data():
        for i in range(total):
            l = np.random.randint(4, 40)
            x = np.random.randint(0, vocab_size, l)
            y = np.random.randint(0, vocab_size, l + random.randint(0, 5))
            yield x, y

    path = Path('tmp.test.multipart.largedb')
    try:
        db = MultipartDb.create(path=path, recs=get_data(), has_id=False,
                                names=['x', 'y'], part_size=total // n_parts,
                                overwrite=True)
        size = sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())
        print(f'{len(db)} rows; {size:,} bytes')
    finally:
        shutil.rmtree(path)


def test_best_type():
    assert best_type(0, 127) == np.uint8, f'{best_type(0, 127) }'
    assert best_type(0, 255) == np.uint8
    assert best_type(-1, 127) == np.int8

    assert best_type(-1, 255) == np.int16
    assert best_type(0, 257) == np.uint16

    assert best_type(0, 16_000) == np.uint16
    assert best_type(0, 32_000) == np.uint16
    assert best_type(0, 65_000) == np.uint16
    assert best_type(0, 66_000) == np.uint32
    assert best_type(0, 2_000_000) == np.uint32
    assert best_type(0, 4_000_000_000) == np.uint32
    assert best_type(0, 5_000_000_000) == np.uint64

    assert best_type(-1, 16_000) == np.int16
    assert best_type(-1, 32_000) == np.int16
    assert best_type(-10, 33_000) == np.int32
    assert best_type(-1, 65_000) == np.int32
    assert best_type(-20, 66_000) == np.int32
    assert best_type(-20, 2_000_000_000) == np.int32
    assert best_type(-20, 3_000_000_000) == np.int64


def test_slices():
    n = 110
    p = 20
    stream = range(n)
    data = list(range(n))
    for i, s in enumerate(MultipartDb.slices(stream, size=p)):
        assert np.array_equal(list(s), data[i * p: (i + 1) * p])
