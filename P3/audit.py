#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import re
from collections import defaultdict

#######################
# Audit Data Elements #
#######################

pattern_lower = re.compile(r'^([a-z]|_)*$')
pattern_lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
pattern_lower_bi_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# count the elements of different tags
def count_tags(datafile):
    tags = {}
    with open(datafile, 'r') as f:
        for event, elem in ET.iterparse(datafile):
            tag = elem.tag
            if tag not in tags:
                tags[tag] = 1
            else:
                tags[tag] += 1
    print(f"""
OSM tag: {tags['osm']};
Node tag: {tags['node']};
Way tag: {tags['way']};
Relaton tag: {tags['relation']}
    """)

# audit keys of tag type elements
def audit_keys(datafile, more=False):
    keys = {'lower': 0, 'lower_colon': 0, 'lower_bi_colon': 0, 'problemchars': 0, 'others': 0}
    with open(datafile, 'r') as f:
        for event, elem in ET.iterparse(datafile):
            if elem.tag == 'tag':
                for tag in elem.iter('tag'):
                    if problemchars.search(elem.attrib['k']):
                        keys['problemchars'] += 1
                        if more == True:
                            print("Problemchars found: ", elem.attrib['k'])
                    elif pattern_lower_colon.search(elem.attrib['k']):
                        keys['lower_colon'] += 1
                    elif pattern_lower_bi_colon.search(elem.attrib['k']):
                        keys['lower_bi_colon'] += 1
                    elif pattern_lower.search(elem.attrib['k']):
                        keys['lower'] += 1
                    else:
                        keys['others'] += 1
    print(f"""
Keys of tag type elements:
{keys['lower']} keys with only alpha characters and '_';
{keys['lower_colon']} keys with alpha characters, '_' and a colon;
{keys['lower_bi_colon']} keys with alpha characters, '_' and two colons;
{keys['problemchars']} keys with problem characters.
{keys['others']} keys with other patterns.
Assign argument more=True to see more.
    """)
    
#####################
# Audit Street Type #
#####################
"""
Common street types of Turkey are:
* Bulvarı - Boulevard
* Caddesi - Street
* Sokak - Street
"""
pattern_street_type = re.compile(r'\b\S+\.?$', re.IGNORECASE)
expected = ["Bulvarı", "Caddesi", "Çıkmazı", "Mahallesi", "Sokak", "Yolları", "Yolu", "Yokuşu", "Avenue", "Road", 
            "Street", "Way"]
street_types = defaultdict(set)

def print_sorted_dict(d):
    keys = sorted(d, key=lambda k: len(d[k]), reverse=True)
    # print top 5 results
    count = 1
    for k in keys:
        if count > 5:
            continue
        v= d[k]
        print("{}: {}, {} items".format(k, v, len(v)))
        count += 1

def count_sorted_dict(d):
    keys = sorted(d, key=lambda k: len(d[k]), reverse=True)
    # print top 5 results
    count = 1
    for k in keys:
        if count > 5:
            continue
        v= d[k]
        print("{}: {} items".format(k, len(v)))
        count += 1

def is_street(tag):
    return tag.attrib['k'] == 'addr:street'

def audit_street_type(street_name, street_types=street_types):
    match = pattern_street_type.search(street_name)
    need_clean = False
    street_type = None
    if match:
        street_type = match.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
            need_clean = True
    return need_clean, street_type
            
def audit_street_types(datafile, more=False):
    with open(datafile, 'r') as f:
        for event, elem in ET.iterparse(f):
            if elem.tag == 'node' or elem.tag == 'way':
                for tag in elem.iter('tag'):
                    if is_street(tag):
                        need_clean, t = audit_street_type(tag.attrib['v'])
    if more == True:
        print_sorted_dict(dict(street_types))
    else:
        count_sorted_dict(dict(street_types))

######################
# Clean Street Names #
######################

mapping = { 'Blv.': 'Bulvarı', 'blv.': 'Bulvarı', 'Bulvar': 'Bulvarı', 'bulvar': 'Bulvarı',
            'Cad': 'Caddesi', 'cad': 'Caddesi', 'Cad.': 'Caddesi', 'cad.': 'Caddesi', 'Cadde': 'Caddesi',
            'Cd.': 'Caddesi', 'cd.': 'Caddesi', 'caddesi': 'Caddesi',
            'Mah.': 'Mahallesi', 'mah.': 'Mahallesi', 'mahallesi': 'Mahallesi',
            'Sk.': 'Sokak', 'sk.': 'Sokak', 'Sok.': 'Sokak', 'sok.': 'Sokak',
            'Sokagi': 'Sokak', 'sokagi': 'Sokak', 'Sokağı': 'Sokak', 'sokağı': 'Sokak',
            'sokak': 'Sokak', 'SOKAK': 'Sokak',
            'Yol': 'Yolları', 'yol': 'Yolları', 'yolları': 'Yolları',
            'Yolu': 'yolu',
            'Ykş.': 'Yokuşu', 'ykş.': 'Yokuşu', 'Yokugu': 'Yokuşu', 'yokugu': 'Yokuşu', 'yokuşu': 'Yokuşu',
            }

def unify_street_name(street, mapping=mapping):
    need_clean, street_type = audit_street_type(street)
    if need_clean:
        if street_type in mapping.keys():
            street = re.sub(street_type, mapping[street_type], street)
    return street

def clean_street_names(d):
    for name, streets in d.items():
        for street in streets:
            better_name = unify_street_name(street, mapping)
            print(f"{street} => {better_name}")

##################
# Audit Postcode #
################## 
"""
Postal codes in Turkey consist of 5 digits.
Starting with the 2 digit license plate code of the provinces
followed by three digits to specify the location within it.
Istanbul code: 34 (41, 81 are also possible)
"""
pattern_postal = re.compile(r'^34|41|81\d{3}$')

def is_postal(tag):
    return tag.attrib['k'] == 'addr:postcode'

def audit_postcode(postcode):
    # remove extra whitespace
    postcode = postcode.strip()
    # validate Istanbul postal code format
    is_valid = re.search(pattern_postal, postcode)
    if not is_valid:
        print(f"Invalid postcode: {postcode}")
    return postcode

def audit_postcodes(datafile):
    with open(datafile, 'r') as f:
        for event, elem in ET.iterparse(datafile):
            if elem.tag == 'node' or elem.tag == 'way':
                for tag in elem.iter('tag'):
                    if is_postal(tag):
                        audit_postcode(tag.attrib['v'])

#######################
# Audit Phone Numbers #
#######################
"""
Turkey local phone numbers: seven digits (3+4)
Turkey country calling code: +90 
Istanbul area codes (European side): 212
Istanbul area codes (Asian side): 216
But this map may cover areas other than these 2,
so we do not validate the area code in the project.
"""
std_phone_format = re.compile(r'^\+90\s\d{3}\s\d{3}\s\d{4}$')
d12_phone_format = re.compile(r'^90\d{10}$')
all_digits = re.compile(r'^\d*$')
miss_cy_code = re.compile(r'^\d{10}$')
miss_area_code = re.compile(r'^90\d{7}$')
miss_codes = re.compile(r'^\d{7}$')

problem_number_type = {'undigits': 0, 'unformated': 0, 'miss_codes': 0,\
                       'miss_cy_code': 0, 'miss_area_code': 0,\
                       'wrong_cy_code': 0, 'zero_cy_code': 0, 'd3_cy_code': 0,\
                       'others': 0}

def is_phone(tag):
    return tag.attrib['k'] == 'contact:phone' or tag.attrib['k'] == 'phone'

def audit_phone_numbers(datafile, more=False):
    count = 0
    with open(datafile, 'r') as f:
        for event, elem in ET.iterparse(datafile):
            if elem.tag == 'node' or elem.tag == 'way':
                for tag in elem.iter('tag'):
                    if is_phone(tag):
                        count += 1
                        # if the phone number match the standard format skip the loop
                        # e.g. +90 212 650 5833
                        if std_phone_format.match(tag.attrib['v']):
                            continue
                        # remove '+' , space and '()'
                        number = tag.attrib['v'].replace('+', '').replace(' ', '').replace('(', '').replace(')', '')
                        # check if the number match 12 digits phone number
                        # e,g, 902126505833
                        if d12_phone_format.match(number):
                            problem_number_type['unformated'] += 1
                        elif not all_digits.match(number):
                            problem_number_type['undigits'] += 1
                        elif miss_cy_code.match(number):
                            problem_number_type['miss_cy_code'] += 1
                        elif miss_area_code.match(number):
                            problem_number_type['miss_area_code'] += 1
                        elif miss_codes.match(number):
                            problem_number_type['miss_codes'] += 1
                        else:
                            problem_number_type['others'] += 1
                            if more == True:
                                print(f"Invalid phone number: {tag.attrib['v']}")

    print(f"""
There are {count} phone numbers in this map:
{problem_number_type['undigits']} numbers are not actually numbers;
{problem_number_type['miss_cy_code']} numbers are missing country code;
{problem_number_type['miss_area_code']} numbers are missing area code;
{problem_number_type['miss_codes']} numbers are missing both country code and area code;
{problem_number_type['unformated']} numbers are not well formated
{problem_number_type['others']} numbers have other problems (e.g. extra zeros, 
wrong country code, more than one phone numbers etc.)
Assign argument more=True to see more.
    """)

#######################
# Clean Phone Numbers #
#######################

def format_phone_number(phone):
    number = f'+{phone[0:2]} {phone[2:5]} {phone[5:8]} {phone[8:]}'
    return number

def remove_pre_zero(phone):
    while phone[0] == '0':
        phone = phone[1:]
    return phone

def update_phone_number(phone):
    # remove '+' , space and '()'
    number = phone.replace('+', '').replace(' ', '').replace('(', '').replace(')', '')
    # remove zeros before the country code
    number = remove_pre_zero(number)
    # not well formatted
    if d12_phone_format.match(number):
        return format_phone_number(number)
    # missing country code
    elif miss_cy_code.match(number):
        number = f'90{number}'
        return format_phone_number(number)
    # wrong country code: 9, 9x or 900
    elif re.match(r'^9\d{10}$', number) or re.match(r'^9\d212|216{7}$', number) or re.match(r'^900\d{10}$', number):
        number = f'90{number[-10:]}'
        return format_phone_number(number)
    else:
        return phone

def clean_phone_numbers(list):
    for item in list:
        better_number = update_phone_number(item)
        print(f"{item} => {better_number}")