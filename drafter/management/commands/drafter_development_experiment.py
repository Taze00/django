import hashlib,json
from pathlib import Path
from django.core.management.base import BaseCommand,CommandError
from drafter.services.development_experiment import run_experiment
from drafter.services.v2_future_window import publish


class Command(BaseCommand):
    def add_arguments(self,parser):
        for name in ('dataset','dataset-sha256','protocol','protocol-sha256','output','revision'):
            parser.add_argument('--'+name,required=True)
    def handle(self,*args,**options):
        if Path(options['output']).exists():raise CommandError('Preserve existing result; no overwrite')
        data=Path(options['dataset']).read_bytes();protocol=Path(options['protocol']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=options['dataset_sha256'] or hashlib.sha256(protocol).hexdigest()!=options['protocol_sha256']:
            raise CommandError('Pinned dataset/protocol byte hash mismatch')
        try:
            result=run_experiment(json.loads(data),json.loads(protocol),options['revision'])
        except ValueError as error:raise CommandError(str(error)) from None
        publish(options['output'],result)
        self.stdout.write(json.dumps({k:v for k,v in result.items() if k!='models'},indent=2,sort_keys=True))
