"""
Management command: import_all_countries
"""
import pycountry
from babel import Locale
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from geo.models import Continent, Country

COUNTRY_CONTINENT = {
    'DZ':'africa','AO':'africa','BJ':'africa','BW':'africa','BF':'africa','BI':'africa','CV':'africa','CM':'africa','CF':'africa','TD':'africa','KM':'africa','CG':'africa','CD':'africa','CI':'africa','DJ':'africa','EG':'africa','GQ':'africa','ER':'africa','SZ':'africa','ET':'africa','GA':'africa','GM':'africa','GH':'africa','GN':'africa','GW':'africa','KE':'africa','LS':'africa','LR':'africa','LY':'africa','MG':'africa','MW':'africa','ML':'africa','MR':'africa','MU':'africa','MA':'africa','MZ':'africa','NA':'africa','NE':'africa','NG':'africa','RW':'africa','ST':'africa','SN':'africa','SL':'africa','SO':'africa','ZA':'africa','SS':'africa','SD':'africa','TZ':'africa','TG':'africa','TN':'africa','UG':'africa','ZM':'africa','ZW':'africa','EH':'africa','RE':'africa','YT':'africa','SH':'africa','IO':'africa','SC':'africa',
    'AL':'europe','AD':'europe','AT':'europe','BY':'europe','BE':'europe','BA':'europe','BG':'europe','HR':'europe','CY':'europe','CZ':'europe','DK':'europe','EE':'europe','FI':'europe','FR':'europe','DE':'europe','GR':'europe','HU':'europe','IS':'europe','IE':'europe','IT':'europe','XK':'europe','LV':'europe','LI':'europe','LT':'europe','LU':'europe','MT':'europe','MD':'europe','MC':'europe','ME':'europe','NL':'europe','MK':'europe','NO':'europe','PL':'europe','PT':'europe','RO':'europe','RU':'europe','SM':'europe','RS':'europe','SK':'europe','SI':'europe','ES':'europe','SE':'europe','CH':'europe','UA':'europe','GB':'europe','VA':'europe','AX':'europe','GI':'europe','GG':'europe','JE':'europe','IM':'europe','SJ':'europe','FO':'europe',
    'AF':'asia','AM':'asia','AZ':'asia','BH':'asia','BD':'asia','BT':'asia','BN':'asia','KH':'asia','CN':'asia','GE':'asia','IN':'asia','ID':'asia','IR':'asia','IQ':'asia','IL':'asia','JP':'asia','JO':'asia','KZ':'asia','KW':'asia','KG':'asia','LA':'asia','LB':'asia','MY':'asia','MV':'asia','MN':'asia','MM':'asia','NP':'asia','KP':'asia','OM':'asia','PK':'asia','PS':'asia','PH':'asia','QA':'asia','SA':'asia','SG':'asia','KR':'asia','LK':'asia','SY':'asia','TW':'asia','TJ':'asia','TH':'asia','TL':'asia','TR':'asia','TM':'asia','AE':'asia','UZ':'asia','VN':'asia','YE':'asia','HK':'asia','MO':'asia',
    'AG':'north-america','BS':'north-america','BB':'north-america','BZ':'north-america','CA':'north-america','CR':'north-america','CU':'north-america','DM':'north-america','DO':'north-america','SV':'north-america','GD':'north-america','GT':'north-america','HT':'north-america','HN':'north-america','JM':'north-america','MX':'north-america','NI':'north-america','PA':'north-america','KN':'north-america','LC':'north-america','VC':'north-america','TT':'north-america','US':'north-america','GL':'north-america','PR':'north-america','VI':'north-america','KY':'north-america','TC':'north-america','BM':'north-america','VG':'north-america','AW':'north-america','CW':'north-america','SX':'north-america','MF':'north-america','GP':'north-america','MQ':'north-america','PM':'north-america','MS':'north-america','AI':'north-america',
    'AR':'south-america','BO':'south-america','BR':'south-america','CL':'south-america','CO':'south-america','EC':'south-america','GY':'south-america','PY':'south-america','PE':'south-america','SR':'south-america','UY':'south-america','VE':'south-america','GF':'south-america','FK':'south-america',
    'AU':'australia','FJ':'australia','KI':'australia','MH':'australia','FM':'australia','NR':'australia','NZ':'australia','PW':'australia','PG':'australia','WS':'australia','SB':'australia','TO':'australia','TV':'australia','VU':'australia','CK':'australia','NU':'australia','NF':'australia','PF':'australia','NC':'australia','WF':'australia','AS':'australia','GU':'australia','MP':'australia','CX':'australia','CC':'australia','TK':'australia',
}

DOMAIN_MAP = {
    'AF':'.af','AL':'.al','DZ':'.dz','AD':'.ad','AO':'.ao','AG':'.com.ag','AR':'.com.ar','AM':'.am','AU':'.com.au','AT':'.at','AZ':'.az','BS':'.bs','BH':'.com.bh','BD':'.com.bd','BB':'.com.bb','BY':'.by','BE':'.be','BZ':'.com.bz','BJ':'.bj','BT':'.bt','BO':'.com.bo','BA':'.ba','BW':'.co.bw','BR':'.com.br','BN':'.com.bn','BG':'.bg','BF':'.bf','BI':'.bi','CV':'.cv','KH':'.com.kh','CM':'.cm','CA':'.ca','CF':'.cf','TD':'.td','CL':'.cl','CN':'.cn','CO':'.com.co','CG':'.cg','CD':'.cd','CR':'.co.cr','HR':'.hr','CU':'.com.cu','CY':'.com.cy','CZ':'.cz','DK':'.dk','DJ':'.dj','DM':'.dm','DO':'.com.do','EC':'.com.ec','EG':'.com.eg','SV':'.com.sv','GQ':'.com.gq','EE':'.ee','SZ':'.co.sz','ET':'.com.et','FJ':'.com.fj','FI':'.fi','FR':'.fr','GA':'.ga','GM':'.gm','GE':'.ge','DE':'.de','GH':'.com.gh','GR':'.gr','GD':'.com.gd','GT':'.com.gt','GN':'.com.gn','GW':'.gw','GY':'.gy','HT':'.ht','HN':'.hn','HK':'.com.hk','HU':'.hu','IS':'.is','IN':'.co.in','ID':'.co.id','IR':'.ir','IQ':'.iq','IE':'.ie','IL':'.co.il','IT':'.it','JM':'.com.jm','JP':'.co.jp','JO':'.jo','KZ':'.kz','KE':'.co.ke','KI':'.ki','KR':'.co.kr','KW':'.com.kw','KG':'.kg','LA':'.la','LV':'.lv','LB':'.com.lb','LS':'.co.ls','LR':'.com.lr','LY':'.com.ly','LI':'.li','LT':'.lt','LU':'.lu','MO':'.com.mo','MG':'.mg','MW':'.mw','MY':'.com.my','MV':'.mv','ML':'.ml','MT':'.com.mt','MR':'.mr','MU':'.mu','MX':'.com.mx','FM':'.fm','MD':'.md','MC':'.mc','MN':'.mn','ME':'.me','MA':'.co.ma','MZ':'.co.mz','MM':'.com.mm','NA':'.com.na','NR':'.nr','NP':'.com.np','NL':'.nl','NZ':'.co.nz','NI':'.com.ni','NE':'.ne','NG':'.com.ng','MK':'.mk','NO':'.no','OM':'.com.om','PK':'.com.pk','PW':'.pw','PS':'.ps','PA':'.com.pa','PG':'.com.pg','PY':'.com.py','PE':'.com.pe','PH':'.com.ph','PL':'.pl','PT':'.pt','PR':'.com.pr','QA':'.com.qa','RO':'.ro','RU':'.ru','RW':'.rw','SM':'.sm','ST':'.st','SA':'.com.sa','SN':'.sn','RS':'.rs','SC':'.sc','SL':'.com.sl','SG':'.com.sg','SK':'.sk','SI':'.si','SB':'.com.sb','SO':'.so','ZA':'.co.za','ES':'.es','LK':'.lk','SR':'.sr','SE':'.se','CH':'.ch','SY':'.sy','TW':'.com.tw','TJ':'.com.tj','TZ':'.co.tz','TH':'.co.th','TL':'.tl','TG':'.tg','TO':'.to','TT':'.tt','TN':'.tn','TR':'.com.tr','TM':'.tm','TV':'.tv','UG':'.co.ug','UA':'.com.ua','AE':'.ae','GB':'.co.uk','US':'.com','UY':'.com.uy','UZ':'.co.uz','VU':'.vu','VE':'.co.ve','VN':'.com.vn','YE':'.com.ye','ZM':'.co.zm','ZW':'.co.zw','GL':'.gl','KY':'.ky',
}

def alpha2_to_flag(a2):
    return ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in a2.upper())

class Command(BaseCommand):
    help = 'Import all world countries'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--update', action='store_true', help='Update name_de/domain/flag on existing countries')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        update = options['update']
        de_territories = Locale('de').territories
        continents = {c.slug: c for c in Continent.objects.all()}
        existing = {c.slug: c for c in Country.objects.all()}
        created = updated = skipped = no_continent = 0

        for country in sorted(pycountry.countries, key=lambda c: c.name):
            a2 = country.alpha_2
            cont_slug = COUNTRY_CONTINENT.get(a2)
            if not cont_slug:
                no_continent += 1
                continue
            continent = continents.get(cont_slug)
            if not continent:
                continue
            name_en = country.name
            name_de = de_territories.get(a2, '') or name_en
            flag = alpha2_to_flag(a2)
            domain = DOMAIN_MAP.get(a2, '')
            slug = slugify(name_en)

            if slug in existing:
                if update:
                    obj = existing[slug]
                    obj.name_de = name_de
                    obj.flag_emoji = flag
                    if domain and not obj.domain:
                        obj.domain = domain
                    if not dry_run:
                        obj.save()
                    self.stdout.write(f'  Updated: {name_en}')
                    updated += 1
                else:
                    skipped += 1
                continue

            self.stdout.write(f'  + {flag} {name_en} ({name_de}) [{cont_slug}] {domain}')
            if not dry_run:
                obj = Country.objects.create(
                    continent=continent, name=name_en, name_de=name_de,
                    slug=slug, flag_emoji=flag, domain=domain, order=100,
                )
                existing[slug] = obj
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done: {created} created, {updated} updated, {skipped} skipped, {no_continent} no continent'
        ))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - nothing saved'))
