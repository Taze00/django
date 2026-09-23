from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('drafter', '0019_tagged_frontier')]
    operations = [
        migrations.AddField(model_name='praxisfall', name='snapshot_key',
                            field=models.CharField(max_length=64, unique=True, null=True, blank=True)),
        migrations.AddField(model_name='praxisfall', name='snapshot_metadata',
                            field=models.JSONField(default=dict, blank=True)),
    ]
