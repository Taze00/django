"""Finite resumable development cycles; no background daemon or model fitting."""
import json
from django.core.management.base import BaseCommand,CommandError
from drafter.services.development_collection import DevelopmentCollector


class Command(BaseCommand):
    def add_arguments(self,parser):
        parser.add_argument('--recover-only',action='store_true',help='Replay retained pending raw without HTTP')
        parser.add_argument('--cycles',type=int,choices=range(1,21),default=4)
        parser.add_argument('--max-battlelogs',type=int,choices=range(1,51),default=50)
        parser.add_argument('--code-revision',required=True)

    def handle(self,*args,**options):
        for cycle in range(options['cycles']):
            try:
                report=DevelopmentCollector(max_battlelogs=0 if options['recover_only'] else options['max_battlelogs'],
                    code_revision=options['code_revision']).execute()
            except ValueError as error:
                raise CommandError(str(error)) from None
            self.stdout.write(json.dumps({'cycle':cycle+1,**report},sort_keys=True))
            self.stdout.flush()
            if not report['next_cycle_allowed'] or not report['battlelog_attempts']:
                break
