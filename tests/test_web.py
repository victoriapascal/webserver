# -*- coding: utf-8 -*-
from minimock import Mock, TraceTracker, assert_same_trace
import websmash
import os
from werkzeug import FileStorage
from websmash.models import Job
from tests.test_shared import WebsmashTestCase

class WebTestCase(WebsmashTestCase):
    def test_startpage(self):
        """Test if startpage has a "Submit Query" button"""
        rv = self.client.get('/')
        assert "Submit" in rv.data

    def test_downloadpage(self):
        """Test if download page works"""
        rv = self.client.get('/download')
        assert "The current standalone release is antiSMASH <strong>3.0.5</strong> (<em>January 20th, 2016</em>)" in rv.data

    def test_helppage(self):
        """Test if help page works"""
        rv = self.client.get('/help')
        assert "antiSMASH input parameters" in rv.data

    def test_aboutpage(self):
        """Test if about page works"""
        rv = self.client.get('/about')
        assert "About antiSMASH" in rv.data

    def test_contactpage(self):
        """Test if contact form is displayed"""
        rv = self.client.get('/contact')
        assert "Contact us if you have questions" in rv.data

    def test_contactpage_no_email(self):
        """Test if contact form complains without an email address"""
        test_body = "Test body"
        rv = self.client.post('/contact', data=dict(body=test_body),
                           follow_redirects=True)
        assert "Please specify an email address" in rv.data
        assert test_body in rv.data

    def test_contactpage_no_message(self):
        """Test if contact form complains without a message"""
        email = "ex@mp.le"
        rv = self.client.post('/contact', data=dict(email=email),
                           follow_redirects=True)
        assert "No message specified. Please specify a message" in rv.data
        assert email in rv.data

    def test_contactpage_sent_mail(self):
        """Test if contact page reports that it sent a message"""
        data = dict(email="ex@mp.le", body="Test body")
        with websmash.mail.record_messages() as outbox:
            rv = self.client.post('/contact', data=data, follow_redirects=True)
            assert "Your message was successfully sent." in rv.data
            assert data['body'] in rv.data
            assert len(outbox) == 2
            contact_msg = outbox[0]
            confirm_msg = outbox[1]
            assert contact_msg.subject == 'antiSMASH feedback'
            assert data['body'] in contact_msg.body
            assert confirm_msg.subject == 'antiSMASH feedback received'
            assert data['body'] in confirm_msg.body

    def test_submit_job_upload(self):
        """Test if submitting a job with an uploaded sequence works"""
        data = dict(seq=self.tmp_file, cluster_1=u'on')
        rv = self.client.post('/', data=data, follow_redirects=True)
        assert "Status of job" in rv.data

    def test_submit_job_download(self):
        """Test if submitting a job with a downloaded sequence works"""
        data = dict(ncbi='TESTING', cluster_1=u'on')
        rv = self.client.post('/', data=data, follow_redirects=True)
        assert "Status of job" in rv.data
        redis_store = self._ctx.g._database
        job_id = redis_store.keys('job:*')[0]
        res = redis_store.hgetall(job_id)
        assert res != {}
        j = Job(**res)
        assert j is not None
        self.assertEquals(j.download, 'TESTING')

    def test_display(self):
        """Test if displaying jobs works as expected"""
        rv = self.client.get('/display/invalid')
        self.assert404(rv)
        j = Job()
        redis_store = self._ctx.g._database
        redis_store.hmset(u"job:%s" % j.uid, j.get_dict())
        rv = self.client.get('/display/%s' % j.uid)
        assert "Status of job" in rv.data

    def test_compat_downloadpage(self):
        """Test if old download page link works"""
        rv = self.client.get('/download.html')
        assert "The current standalone release is antiSMASH <strong>3.0.5</strong> (<em>January 20th, 2016</em>)" in rv.data

    def test_compat_helppage(self):
        """Test if old help page link works"""
        rv = self.client.get('/help.html')
        assert "antiSMASH input parameters" in rv.data

    def test_compat_aboutpage(self):
        """Test if old about page link works"""
        rv = self.client.get('/about.html')
        assert "About antiSMASH" in rv.data

    def test_compat_contactpage(self):
        """Test if old contact form link works"""
        rv = self.client.get('/contact.html')
        assert "Contact us if you have questions" in rv.data

    def test_compat_contactpage_sent_mail(self):
        """Test if contact page reports that it sent a message"""
        data = dict(email="ex@mp.le", body="Test body")
        with websmash.mail.record_messages() as outbox:
            rv = self.client.post('/contact.html', data=data, follow_redirects=True)
            assert "Your message was successfully sent." in rv.data
            assert data['body'] in rv.data
            assert len(outbox) == 2
            contact_msg = outbox[0]
            confirm_msg = outbox[1]
            assert contact_msg.subject == 'antiSMASH feedback'
            assert data['body'] in contact_msg.body
            assert confirm_msg.subject == 'antiSMASH feedback received'
            assert data['body'] in confirm_msg.body
