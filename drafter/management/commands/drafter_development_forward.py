import hashlib
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from drafter.services.development_forward import forward_check
from drafter.services.v2_future_window import publish


class Command(BaseCommand):
    def add_arguments(self,parser):
        for name in ('protocol','protocol-sha256','output','revision'):
            parser.add_argument('--'+name,required=True)

    def handle(self,*args,**options):
        if Path(options['output']).exists():
            raise CommandError('Preserve existing forward result; no overwrite')
        body=Path(options['protocol']).read_bytes()
        if hashlib.sha256(body).hexdigest()!=options['protocol_sha256']:
            raise CommandError('Pinned forward protocol byte hash mismatch')
        try:
            result=forward_check(json.loads(body),options['revision'])
        except ValueError as error:
            raise CommandError(str(error)) from None
        publish(options['output'],result)
        self.stdout.write(json.dumps({k:v for k,v in result.items() if k!='members'},indent=2,sort_keys=True))
