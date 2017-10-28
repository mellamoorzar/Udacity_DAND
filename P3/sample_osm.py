# Use the following code to take a systematic sample of elements from your original OSM region.
# Try changing the value of k so that your resulting SAMPLE_FILE ends up at different sizes.
# When starting out, try using a larger k, then move on to an intermediate k before processing your whole dataset.

import xml.etree.ElementTree as ET

def get_element(file, tags=('node', 'way', 'relation')):
    """
    yield element if it is the right type of tag
    
    reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

def gen_sample(file_in, file_out, k):
    # parameter k: take every k-th top level element
    
    with open(file_out, 'wb') as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write('<osm>\n  ')
        
        # Write every k-th top level element
        for i, element in enumerate(get_element(file_in)):
            if i % k == 0:
                output.write(ET.tostring(element, encoding='utf-8'))
        
        output.write('</osm>')