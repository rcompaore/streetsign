'''
    First file on the noble epic tast of unit testing.
'''

import sys
import os
import tempfile
import unittest
import html5lib
from datetime import datetime
from peewee import SqliteDatabase, create_model_tables
from flask import json, url_for

sys.path.append(os.path.dirname(__file__) + '/..')

import streetsign_server
import streetsign_server.models as models
from streetsign_server.models import Post, Feed

from unittest_helpers import StreetSignTestCase

class TestSetup(StreetSignTestCase):
    ''' First basic sanity checks '''

    def test_empty_db(self):
        ''' test that with the new database, there are no posts. '''

        request = self.client.get('/')
        assert 'Dashboard' in request.data # it is the front page
        assert 'Login' in request.data # not logged in

        request = self.client.get('/posts/')
        assert '<span class="post_count">No Posts at all!' in request.data

class TestDB(StreetSignTestCase):
    ''' test basic database interactions '''
    def test_empty(self):
        self.assertEqual(models.Post.select().count(), 0)
        self.assertEqual(models.Feed.select().count(), 0)

    def test_create_basics(self):
        f = models.Feed.create(name='first feed')
        self.assertEqual(models.Feed.select().count(), 1)

        u = models.User.create(name='test user', loginname='test', emailaddress='test@example.com',
            passwordhash='')
        u.set_password('test pass')

        p = models.Post.create(feed=f, type='html', content='{"content":"text"}', author=u)

        # make sure times have sane defaults:

        self.assertTrue(p.active_start < datetime.now())
        self.assertTrue(p.active_end > datetime.now())
        self.assertEqual(p.active_status(), 'now')

        # make sure we can select it directly:

        self.assertEqual(models.Post.select().count(), 1)

        # make sure the feed has it available:

        self.assertEqual(f.posts.count(), 1)

        # check that our views are displaying it correctly...

        # we need to save(), as the views use different (joined) queries, which aren't cached/using this transaction's data.

        p.save()
        f.save()

        # check that first there are no posts:

        self.assertEqual(json.loads(self.client.get('/screens/posts_from_feeds/%5B' + str(f.id) + '%5D').data),
                         {'posts':[]})

        # set published, and try again:

        p.published = True

        p.save()
        f.save()

        posts_list = json.loads(self.client.get('/screens/posts_from_feeds/%5B' + str(f.id) + '%5D').data)['posts']
        self.assertEqual(len(posts_list), 1)

        # now try retrieving the post as json, and comparing it to our local database retrieved version:

        from_server = json.loads(self.client.get(posts_list[0]['uri']).data)
        self.assertEqual(from_server, json.loads(json.dumps(p.dict_repr())))

if __name__ == '__main__':
    unittest.main()
