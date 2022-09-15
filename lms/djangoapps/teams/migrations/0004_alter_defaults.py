# Generated by Django 1.11.29 on 2020-03-18 15:36


import django_countries.fields
from django.db import migrations, models

import lms.djangoapps.teams.models
from common.djangoapps.student.models import models as student_models


class Migration(migrations.Migration):
    dependencies = [
        ('teams', '0003_courseteam_organization_protected'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseteam',
            name='country',
            field=django_countries.fields.CountryField(blank=True, default='', max_length=2),
        ),
        migrations.AlterField(
            model_name='courseteam',
            name='language',
            field=student_models.LanguageField(blank=True, choices=[['aa', 'Afar'], ['ab', 'Abkhazian'], ['af', 'Afrikaans'], ['ak', 'Akan'], ['sq', 'Albanian'], ['am', 'Amharic'], ['ar', 'Arabic'], ['an', 'Aragonese'], ['hy', 'Armenian'], ['as', 'Assamese'], ['av', 'Avaric'], ['ae', 'Avestan'], ['ay', 'Aymara'], ['az', 'Azerbaijani'], ['ba', 'Bashkir'], ['bm', 'Bambara'], ['eu', 'Basque'], ['be', 'Belarusian'], ['bn', 'Bengali'], ['bh', 'Bihari languages'], ['bi', 'Bislama'], ['bs', 'Bosnian'], ['br', 'Breton'], ['bg', 'Bulgarian'], ['my', 'Burmese'], ['ca', 'Catalan'], ['ch', 'Chamorro'], ['ce', 'Chechen'], ['zh', 'Chinese'], ['zh_HANS', 'Simplified Chinese'], ['zh_HANT', 'Traditional Chinese'], ['cu', 'Church Slavic'], ['cv', 'Chuvash'], ['kw', 'Cornish'], ['co', 'Corsican'], ['cr', 'Cree'], ['cs', 'Czech'], ['da', 'Danish'], ['dv', 'Divehi'], ['nl', 'Dutch'], ['dz', 'Dzongkha'], ['en', 'English'], ['eo', 'Esperanto'], ['et', 'Estonian'], ['ee', 'Ewe'], ['fo', 'Faroese'], ['fj', 'Fijian'], ['fi', 'Finnish'], ['fr', 'French'], ['fy', 'Western Frisian'], ['ff', 'Fulah'], ['ka', 'Georgian'], ['de', 'German'], ['gd', 'Gaelic'], ['ga', 'Irish'], ['gl', 'Galician'], ['gv', 'Manx'], ['el', 'Greek'], ['gn', 'Guarani'], ['gu', 'Gujarati'], ['ht', 'Haitian'], ['ha', 'Hausa'], ['he', 'Hebrew'], ['hz', 'Herero'], ['hi', 'Hindi'], ['ho', 'Hiri Motu'], ['hr', 'Croatian'], ['hu', 'Hungarian'], ['ig', 'Igbo'], ['is', 'Icelandic'], ['io', 'Ido'], ['ii', 'Sichuan Yi'], ['iu', 'Inuktitut'], ['ie', 'Interlingue'], ['ia', 'Interlingua'], ['id', 'Indonesian'], ['ik', 'Inupiaq'], ['it', 'Italian'], ['jv', 'Javanese'], ['ja', 'Japanese'], ['kl', 'Kalaallisut'], ['kn', 'Kannada'], ['ks', 'Kashmiri'], ['kr', 'Kanuri'], ['kk', 'Kazakh'], ['km', 'Central Khmer'], ['ki', 'Kikuyu'], ['rw', 'Kinyarwanda'], ['ky', 'Kirghiz'], ['kv', 'Komi'], ['kg', 'Kongo'], ['ko', 'Korean'], ['kj', 'Kuanyama'], ['ku', 'Kurdish'], ['lo', 'Lao'], ['la', 'Latin'], ['lv', 'Latvian'], ['li', 'Limburgan'], ['ln', 'Lingala'], ['lt', 'Lithuanian'], ['lb', 'Luxembourgish'], ['lu', 'Luba-Katanga'], ['lg', 'Ganda'], ['mk', 'Macedonian'], ['mh', 'Marshallese'], ['ml', 'Malayalam'], ['mi', 'Maori'], ['mr', 'Marathi'], ['ms', 'Malay'], ['mg', 'Malagasy'], ['mt', 'Maltese'], ['mn', 'Mongolian'], ['na', 'Nauru'], ['nv', 'Navajo'], ['nr', 'Ndebele, South'], ['nd', 'Ndebele, North'], ['ng', 'Ndonga'], ['ne', 'Nepali'], ['nn', 'Norwegian Nynorsk'], ['nb', 'Bokmål, Norwegian'], ['no', 'Norwegian'], ['ny', 'Chichewa'], ['oc', 'Occitan'], ['oj', 'Ojibwa'], ['or', 'Oriya'], ['om', 'Oromo'], ['os', 'Ossetian'], ['pa', 'Panjabi'], ['fa', 'Persian'], ['pi', 'Pali'], ['pl', 'Polish'], ['pt', 'Portuguese'], ['ps', 'Pushto'], ['qu', 'Quechua'], ['rm', 'Romansh'], ['ro', 'Romanian'], ['rn', 'Rundi'], ['ru', 'Russian'], ['sg', 'Sango'], ['sa', 'Sanskrit'], ['si', 'Sinhala'], ['sk', 'Slovak'], ['sl', 'Slovenian'], ['se', 'Northern Sami'], ['sm', 'Samoan'], ['sn', 'Shona'], ['sd', 'Sindhi'], ['so', 'Somali'], ['st', 'Sotho, Southern'], ['es', 'Spanish'], ['sc', 'Sardinian'], ['sr', 'Serbian'], ['ss', 'Swati'], ['su', 'Sundanese'], ['sw', 'Swahili'], ['sv', 'Swedish'], ['ty', 'Tahitian'], ['ta', 'Tamil'], ['tt', 'Tatar'], ['te', 'Telugu'], ['tg', 'Tajik'], ['tl', 'Tagalog'], ['th', 'Thai'], ['bo', 'Tibetan'], ['ti', 'Tigrinya'], ['to', 'Tonga (Tonga Islands)'], ['tn', 'Tswana'], ['ts', 'Tsonga'], ['tk', 'Turkmen'], ['tr', 'Turkish'], ['tw', 'Twi'], ['ug', 'Uighur'], ['uk', 'Ukrainian'], ['ur', 'Urdu'], ['uz', 'Uzbek'], ['ve', 'Venda'], ['vi', 'Vietnamese'], ['vo', 'Volapük'], ['cy', 'Welsh'], ['wa', 'Walloon'], ['wo', 'Wolof'], ['xh', 'Xhosa'], ['yi', 'Yiddish'], ['yo', 'Yoruba'], ['za', 'Zhuang'], ['zu', 'Zulu']], default='', help_text='Optional language the team uses as ISO 639-1 code.', max_length=16),
        ),
        migrations.AlterField(
            model_name='courseteam',
            name='last_activity_at',
            field=models.DateTimeField(db_index=True, default=lms.djangoapps.teams.models.utc_now),
        ),
        migrations.AlterField(
            model_name='courseteam',
            name='topic_id',
            field=models.CharField(blank=True, db_index=True, default='', max_length=255),
        ),
    ]
