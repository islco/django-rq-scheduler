# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase

import factory
import pytz
from django_rq import job
from scheduler.models import RepeatableJob, ScheduledJob


class ScheduledJobFactory(factory.Factory):

    name = factory.Sequence(lambda n: 'Addition {}'.format(n))
    job_id = None
    queue = 'default'
    callable = 'scheduler.tests.test_job'
    enabled = True

    @factory.lazy_attribute
    def scheduled_time(self):
        return datetime.now() + timedelta(days=1)

    class Meta:
        model = ScheduledJob


class RepeatableJobFactory(factory.Factory):

    name = factory.Sequence(lambda n: 'Addition {}'.format(n))
    job_id = None
    queue = 'default'
    callable = 'scheduler.tests.test_job'
    enabled = True
    interval = 1
    interval_unit = 'hours'
    repeat = None

    @factory.lazy_attribute
    def scheduled_time(self):
        return datetime.now() + timedelta(minutes=1)

    class Meta:
        model = RepeatableJob


@job
def test_job():
    return 1 + 1


test_non_callable = 'I am a teapot'


class TestScheduledJob(TestCase):

    JobClass = ScheduledJob
    JobClassFactory = ScheduledJobFactory

    def test_callable_func(self):
        job = self.JobClass()
        job.callable = 'scheduler.tests.test_job'
        func = job.callable_func()
        self.assertEqual(test_job, func)

    def test_callable_func_not_callable(self):
        job = self.JobClass()
        job.callable = 'scheduler.tests.test_non_callable'
        with self.assertRaises(TypeError):
            job.callable_func()

    def test_clean_callable(self):
        job = self.JobClass()
        job.callable = 'scheduler.tests.test_job'
        assert job.clean_callable() is None

    def test_clean_callable_invalid(self):
        job = self.JobClass()
        job.callable = 'scheduler.tests.test_non_callable'
        with self.assertRaises(ValidationError):
            job.clean_callable()

    def test_clean(self):
        job = self.JobClass()
        job.queue = settings.RQ_QUEUES.keys()[0]
        job.callable = 'scheduler.tests.test_job'
        assert job.clean() is None

    def test_clean_invalid(self):
        job = self.JobClass()
        job.queue = settings.RQ_QUEUES.keys()[0]
        job.callable = 'scheduler.tests.test_non_callable'
        with self.assertRaises(ValidationError):
            job.clean()

    def test_clean_queue_invalid(self):
        job = self.JobClass()
        job.queue = 'xxxxxx'
        job.callable = 'scheduler.tests.test_job'
        with self.assertRaises(ValidationError):
            job.clean()

    def test_is_schedulable_already_scheduled(self):
        job = self.JobClass()
        job.job_id = 'something'
        self.assertFalse(job.is_schedulable())

    def test_is_schedulable_disabled(self):
        job = self.JobClass()
        job.id = 1
        job.enabled = False
        self.assertFalse(job.is_schedulable())

    def test_is_schedulable_enabled(self):
        job = self.JobClass()
        job.id = 1
        job.enabled = True
        self.assertTrue(job.is_schedulable())

    def test_schedule(self):
        job = self.JobClassFactory()
        job.id = 1
        successful = job.schedule()
        self.assertTrue(successful)
        self.assertIsNotNone(job.job_id)

    def test_unschedulable(self):
        job = self.JobClassFactory()
        job.enabled = False
        successful = job.schedule()
        self.assertFalse(successful)
        self.assertIsNone(job.job_id)

    def test_unschedule(self):
        job = self.JobClassFactory()
        job.job_id = 'something'
        successful = job.unschedule()
        self.assertTrue(successful)
        self.assertIsNone(job.job_id)

    def test_unschedule_not_scheduled(self):
        job = self.JobClassFactory()
        successful = job.unschedule()
        self.assertTrue(successful)
        self.assertIsNone(job.job_id)

    def test_schedule_time_utc(self):
        job = self.JobClass()
        est = pytz.timezone('US/Eastern')
        scheduled_time = datetime(2016, 12, 25, 8, 0, 0, tzinfo=est)
        job.scheduled_time = scheduled_time
        utc = pytz.timezone('UTC')
        expected = scheduled_time.astimezone(utc).isoformat()
        self.assertEqual(expected, job.schedule_time_utc().isoformat())

    def test_save_enabled(self):
        job = self.JobClassFactory()
        job.save()
        self.assertIsNotNone(job.job_id)

    def test_save_disabled(self):
        job = self.JobClassFactory()
        job.save()
        job.enabled = False
        job.save()
        self.assertIsNone(job.job_id)


class TestRepeatableJob(TestScheduledJob):

    JobClass = RepeatableJob
    JobClassFactory = RepeatableJobFactory

    def test_interval_seconds_weeks(self):
        job = RepeatableJob()
        job.interval = 2
        job.interval_unit = 'weeks'
        self.assertEqual(1209600.0, job.interval_seconds())

    def test_interval_seconds_days(self):
        job = RepeatableJob()
        job.interval = 2
        job.interval_unit = 'days'
        self.assertEqual(172800.0, job.interval_seconds())

    def test_interval_seconds_hours(self):
        job = RepeatableJob()
        job.interval = 2
        job.interval_unit = 'hours'
        self.assertEqual(7200.0, job.interval_seconds())

    def test_interval_seconds_minutes(self):
        job = RepeatableJob()
        job.interval = 15
        job.interval_unit = 'minutes'
        self.assertEqual(900.0, job.interval_seconds())

    def test_repeatable_schedule(self):
        job = self.JobClassFactory()
        job.id = 1
        successful = job.schedule()
        self.assertTrue(successful)
        self.assertIsNotNone(job.job_id)

    def test_repeatable_unschedulable(self):
        job = self.JobClassFactory()
        job.enabled = False
        successful = job.schedule()
        self.assertFalse(successful)
        self.assertIsNone(job.job_id)
