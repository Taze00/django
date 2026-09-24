"""Audit exact Legacy bundle prerequisites, no aggregation/model fitting."""
import hashlib
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.conf import settings
from drafter.services.v2_legacy_bundle import preflight

PINNED_ARTIFACT = '92e0b427bf9abce62e047419ea1008f740c9ee7b39b1458ae15692402b7cf52d'


class Command(BaseCommand):
    help = 'Read-only Train and exact Legacy prior lineage audit; never asserts verification by runtime hash'

    def handle(self,*args,**options):
        try:
            body=Path(getattr(settings, 'DRAFTER_V2_MODEL_PATH', Path(settings.BASE_DIR) / 'data/brawl_reports/v2_challenger.json')).read_bytes()
            if hashlib.sha256(body).hexdigest()!=PINNED_ARTIFACT:
                raise ValueError('Selected frozen artifact changed')
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
                report=preflight(json.loads(body))
            self.stdout.write(json.dumps(report,sort_keys=True,indent=2))
        except (ValueError,KeyError,OSError) as error:
            raise CommandError(str(error)) from error
