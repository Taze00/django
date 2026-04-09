from django.core.management.base import BaseCommand
from geo.models import Country, Continent

COUNTRY_DE = {
    'Alaska': 'Alaska',
    'Albania': 'Albanien',
    'American Samoa': 'Amerikanisch-Samoa',
    'Andorra': 'Andorra',
    'Argentina': 'Argentinien',
    'Australia': 'Australien',
    'Austria': 'Österreich',
    'Azores': 'Azoren',
    'Bangladesh': 'Bangladesch',
    'Belarus': 'Belarus',
    'Belgium': 'Belgien',
    'Bermuda': 'Bermuda',
    'Bhutan': 'Bhutan',
    'Bolivia': 'Bolivien',
    'Botswana': 'Botswana',
    'Brazil': 'Brasilien',
    'British Indian Ocean Territory': 'Britisches Territorium im Indischen Ozean',
    'Bulgaria': 'Bulgarien',
    'Cambodia': 'Kambodscha',
    'Canada': 'Kanada',
    'Chile': 'Chile',
    'China': 'China',
    'Christmas Island': 'Weihnachtsinsel',
    'Cocos Islands': 'Kokosinseln',
    'Colombia': 'Kolumbien',
    'Costa Rica': 'Costa Rica',
    'Croatia': 'Kroatien',
    'Curacao': 'Curaçao',
    'Curaçao': 'Curaçao',
    'Cyprus': 'Zypern',
    'Czechia': 'Tschechien',
    'Denmark': 'Dänemark',
    'Dominican Republic': 'Dominikanische Republik',
    'Ecuador': 'Ecuador',
    'Egypt': 'Ägypten',
    'Estonia': 'Estland',
    'Eswatini': 'Eswatini',
    'Falkland Islands': 'Falklandinseln',
    'Faroe Islands': 'Färöer',
    'Finland': 'Finnland',
    'France': 'Frankreich',
    'Germany': 'Deutschland',
    'Ghana': 'Ghana',
    'Gibraltar': 'Gibraltar',
    'Greece': 'Griechenland',
    'Greenland': 'Grönland',
    'Guam': 'Guam',
    'Guatemala': 'Guatemala',
    'Hawaii': 'Hawaii',
    'Hong Kong': 'Hongkong',
    'Hungary': 'Ungarn',
    'Iceland': 'Island',
    'India': 'Indien',
    'Indonesia': 'Indonesien',
    'Iraq': 'Irak',
    'Ireland': 'Irland',
    'Isle of Man': 'Isle of Man',
    'Israel & the West Bank': 'Israel & Westjordanland',
    'Italy': 'Italien',
    'Japan': 'Japan',
    'Jersey': 'Jersey',
    'Jordan': 'Jordanien',
    'Kazakhstan': 'Kasachstan',
    'Kenya': 'Kenia',
    'Kyrgyzstan': 'Kirgisistan',
    'Laos': 'Laos',
    'Latvia': 'Lettland',
    'Lebanon': 'Libanon',
    'Lesotho': 'Lesotho',
    'Liechtenstein': 'Liechtenstein',
    'Lithuania': 'Litauen',
    'Luxembourg': 'Luxemburg',
    'Macau': 'Macau',
    'Madagascar': 'Madagaskar',
    'Madeira': 'Madeira',
    'Malaysia': 'Malaysia',
    'Mali': 'Mali',
    'Malta': 'Malta',
    'Martinique': 'Martinique',
    'Mexico': 'Mexiko',
    'Monaco': 'Monaco',
    'Mongolia': 'Mongolei',
    'Montenegro': 'Montenegro',
    'Namibia': 'Namibia',
    'Nepal': 'Nepal',
    'Netherlands': 'Niederlande',
    'New Zealand': 'Neuseeland',
    'Nigeria': 'Nigeria',
    'North Macedonia': 'Nordmazedonien',
    'Northern Mariana Islands': 'Nördliche Marianen',
    'Norway': 'Norwegen',
    'Oman': 'Oman',
    'Pakistan': 'Pakistan',
    'Panama': 'Panama',
    'Peru': 'Peru',
    'Philippines': 'Philippinen',
    'Pitcairn Islands': 'Pitcairninseln',
    'Poland': 'Polen',
    'Portugal': 'Portugal',
    'Puerto Rico': 'Puerto Rico',
    'Qatar': 'Katar',
    'Reunion': 'Réunion',
    'Romania': 'Rumänien',
    'Russia': 'Russland',
    'Rwanda': 'Ruanda',
    'Saint Pierre and Miquelon': 'Saint-Pierre und Miquelon',
    'San Marino': 'San Marino',
    'Senegal': 'Senegal',
    'Serbia': 'Serbien',
    'Singapore': 'Singapur',
    'Slovakia': 'Slowakei',
    'Slovenia': 'Slowenien',
    'South Africa': 'Südafrika',
    'South Georgia & Sandwich Islands': 'Südgeorgien und Sandwichinseln',
    'South Korea': 'Südkorea',
    'Spain': 'Spanien',
    'Sri Lanka': 'Sri Lanka',
    'Svalbard': 'Spitzbergen',
    'Sweden': 'Schweden',
    'Switzerland': 'Schweiz',
    'São Tomé and Príncipe': 'São Tomé und Príncipe',
    'Taiwan': 'Taiwan',
    'Tanzania': 'Tansania',
    'Thailand': 'Thailand',
    'Tunisia': 'Tunesien',
    'Turkey': 'Türkei',
    'US Minor Outlying Islands': 'Amerikanische Außeninseln',
    'US Virgin Islands': 'Amerikanische Jungferninseln',
    'Uganda': 'Uganda',
    'Ukraine': 'Ukraine',
    'United Arab Emirates': 'Vereinigte Arabische Emirate',
    'United Kingdom': 'Vereinigtes Königreich',
    'United States of America': 'Vereinigte Staaten',
    'Uruguay': 'Uruguay',
    'Vanuatu': 'Vanuatu',
    'Vietnam': 'Vietnam',
}

CONTINENT_DE = {
    'Africa': 'Afrika',
    'Afrika': 'Afrika',
    'Europe': 'Europa',
    'Europa': 'Europa',
    'Asia': 'Asien',
    'North America': 'Nordamerika',
    'Nordamerika': 'Nordamerika',
    'South America': 'Südamerika',
    'Südamerika': 'Südamerika',
    'Australia': 'Australien & Ozeanien',
    'Oceania': 'Australien & Ozeanien',
}


class Command(BaseCommand):
    help = 'Set German names for countries and continents'

    def handle(self, *args, **kwargs):
        updated = 0
        skipped = 0
        for country in Country.objects.all():
            de = COUNTRY_DE.get(country.name)
            if de:
                country.name_de = de
                country.save(update_fields=['name_de'])
                updated += 1
            else:
                self.stdout.write(f'  No DE name for: {country.name}')
                skipped += 1
        self.stdout.write(self.style.SUCCESS(f'Countries: {updated} updated, {skipped} skipped'))

        for continent in Continent.objects.all():
            de = CONTINENT_DE.get(continent.name)
            if de:
                continent.name_de = de
                continent.save(update_fields=['name_de'])
                self.stdout.write(f'  Continent: {continent.name} -> {de}')
            else:
                self.stdout.write(f'  No DE name for continent: {continent.name}')
        self.stdout.write(self.style.SUCCESS('Done'))
