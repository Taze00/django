"""Read-only development membership/coverage; no training or performance metrics."""
import json
from django.core.management.base import BaseCommand
from django.db import connection,transaction
from drafter.services.development_dataset import versioned_development_dataset,chronological_plan
from drafter.services.v2_future_window import publish


class Command(BaseCommand):
    def add_arguments(self,parser):
        parser.add_argument('--output',required=True,help='New private manifest path; never overwrite')

    def handle(self,*args,**options):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            manifest=versioned_development_dataset()
        manifest['chronological_plan']=chronological_plan(manifest)
        publish(options['output'],manifest)
        self.stdout.write(json.dumps({'dataset_sha256':manifest['dataset_sha256'],
            'original_train_n':6094,**manifest['report'],
            'chronological_plan':{k:v for k,v in manifest['chronological_plan'].items() if 'fingerprints' not in k}},indent=2,sort_keys=True))
