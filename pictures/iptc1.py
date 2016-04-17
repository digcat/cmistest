from iptcinfo import IPTCInfo
import sys

fn = (len(sys.argv) > 1 and [sys.argv[1]] or ['test.jpg'])[0]
fn2 = (len(sys.argv) > 2 and [sys.argv[2]] or ['test_out.jpg'])[0]

# Create new info object
info = IPTCInfo(fn)

# Check if file had IPTC data
if len(info.data) < 4: raise Exception(info.error)

# Print list of keywords, supplemental categories, contacts
print "KEYWORDS"
print info.keywords
print "SUPPLEMENTAL"
print info.supplementalCategories
print "CONTACTS"
print info.contacts
print "DATA"
print info.data

# Get specific attributes...
caption = info.data['caption/abstract']

# Create object for file that may does have IPTC data.
# info = IPTCInfo(fn)
# for files without IPTC data, use
info = IPTCInfo(fn, force=True)

# Add/change an attribute
info.data['caption/abstract'] = 'Witty caption here'
info.data['supplemental category'] = ['portrait']

try:
    info.save()
    info.saveAs(fn2)
    print IPTCInfo(fn2)
except:
    print "Couldnt Update the file"
