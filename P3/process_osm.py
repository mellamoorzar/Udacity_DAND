#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Transform osm to csv file. Parse, clean and shape data.

The process for this transformation is as follows:
- Use iterparse to iteratively step through each top level element in the XML
- Clean and shape each element into several data structures using a custom function
- Utilize a schema and validation library to ensure the transformed data is in the correct format
- Write each data structure to the appropriate .csv files
"""
import csv
import codecs
import re
import xml.etree.cElementTree as ET
import schema
import cerberus
from audit import *

PATH = './Data/'

NODES = 'nodes.csv'
NODE_TAGS = 'nodes_tags.csv'
WAYS = 'ways.csv'
WAY_NODES = 'ways_nodes.csv'
WAY_TAGS = 'ways_tags.csv'

NODES_PATH = PATH + NODES
NODE_TAGS_PATH = PATH + NODE_TAGS
WAYS_PATH = PATH + WAYS
WAY_NODES_PATH = PATH + WAY_NODES
WAY_TAGS_PATH = PATH + WAY_TAGS

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

def extract_tag(tag):
    """Clean and extract type, key and value from tag"""
    
    # clean street name and phone number
    if is_street(tag):
        tag_value = unify_street_name(tag.attrib['v'])
    elif is_phone(tag):
        tag_value = update_phone_number(tag.attrib['v'])
    else:
        tag_value = tag.attrib['v']
        
    # deal with colon in key
    if ':' in tag.attrib['k']:
        tag_type = tag.attrib['k'].split(':', 1)[0]
        tag_key = tag.attrib['k'].split(':', 1)[1]
    else:
        tag_type = 'regular'
        tag_key = tag.attrib['k']
    return tag_type, tag_key, tag_value

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        for attr in node_attr_fields:
            node_attribs[attr] = element.attrib[attr]
        
        for child in element:
            node_tag = {}
            
            if problem_chars.match(child.attrib['k']):
                continue
            
            tag_type, tag_key, tag_value = extract_tag(child)
            
            node_tag['id'] = element.attrib['id']
            node_tag['value'] = tag_value
            node_tag['type'] = tag_type
            node_tag['key'] = tag_key

            tags.append(node_tag)
        
        return {'node': node_attribs, 'node_tags': tags}
    
    elif element.tag == 'way':
        for attr in way_attr_fields:
            way_attribs[attr] = element.attrib[attr]
        
        nd_position = 0
        for child in element:
            if child.tag == 'tag':
                way_tag = {}
                
                if problem_chars.match(child.attrib['k']):
                    continue
                    
                tag_type, tag_key, tag_value = extract_tag(child)

                way_tag['id'] = element.attrib['id']
                way_tag['value'] = tag_value
                way_tag['type'] = tag_type
                way_tag['key'] = tag_key
                
                tags.append(way_tag)
            
            elif child.tag == 'nd':
                way_node = {}
                way_node['id'] = element.attrib['id']
                way_node['node_id'] = child.attrib['ref']
                way_node['position'] = nd_position
                nd_position += 1
                
                way_nodes.append(way_node)
            
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
    
# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.items())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))

# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate=False):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w', 'utf-8') as nodes_file,\
    codecs.open(NODE_TAGS_PATH, 'w', 'utf-8') as nodes_tags_file,\
    codecs.open(WAYS_PATH, 'w', 'utf-8') as ways_file,\
    codecs.open(WAY_NODES_PATH, 'w', 'utf-8') as way_nodes_file,\
    codecs.open(WAY_TAGS_PATH, 'w', 'utf-8') as way_tags_file:
        
        nodes_writer = csv.DictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = csv.DictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = csv.DictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = csv.DictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = csv.DictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()
        
        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])