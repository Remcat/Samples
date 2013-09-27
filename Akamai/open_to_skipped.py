try:
	import pubcookie.client
except:
    raise Exception ("""
----------------------------------------------------------------------
You must install the pubcookie package for access to bugzilla or
bart.  Please sudo the following command:

    easy_install -f http://info.akamai.com/~ps/custserv/ps/project/lib/python/trunk/dist/ akapslib

and try again.
----------------------------------------------------------------------
""")
try:
    import MySQLdb
except:
    raise Exception ("""
----------------------------------------------------------------------
You must install the python-mysqldb package for access to bugzilla or
bart.  Please sudo the following command:

    apt-get install python-mysqldb

and try again.
----------------------------------------------------------------------
""")
import os, sys, cookielib, urllib, urllib2, csv
import argparse, time

def authenticate():

  user  = args.username or raw_input("please enter your (weblogin) username: ")
  pswd  = args.password or raw_input("please enter your (weblogin) password: ")
  cjar  = cookielib.CookieJar()
  pubck = pubcookie.client.Client('weblogin.akamai.com', cookiejar=cjar)
  pubck.login(user, pswd)
  pubck.bind('https://release.akamai.com')
  
  cookie_vals = []
  for cookie in cjar:
    cookie_vals.append(cookie.value) 
  return cookie_vals

def find_bugs(lines):
  bugs = []
  for l in lines:
    working_line = l.split(',')
    if working_line[8] == 'VERIFIED':
      if working_line[9] == 'FIXED':
        if working_line[11] == '1':
          bugs.append(working_line[0])
  return bugs

parser = argparse.ArgumentParser()
parser.add_argument("-r", '--release')
parser.add_argument("-u", '--username')
parser.add_argument("-p", '--password')
parser.add_argument("-get_list_only", action='store_true')
args = parser.parse_args()

modify_cr_statuses = not args.get_list_only
release            = args.release  or raw_input("please enter a release number (i.e. 5046): ")

conn     = MySQLdb.connect(host = "release.akamai.com", user = "read_only", db = "release_management")
cursor   = conn.cursor()
query_for_releaseid = 'select releaseid \
				from releases r\
				     join releasestatus rs\
				          on r.releasestatusid = rs.releasestatusid\
				where releasenumber = %s %s order by datecreated desc limit 1;'

cursor.execute(query_for_releaseid % (release, "and releasestatusname = 'active'"))
row      = cursor.fetchall()
cols     = [ d[0] for d in cursor.description ]
current  = dict(zip(cols, row))
cursor.execute(query_for_releaseid % (str(int(release)-1), "and releasestatusname = 'complete'") )
row      = cursor.fetchall()
cols     = [ d[0] for d in cursor.description ]
previous = dict(zip(cols, row))

#cursor   = conn.cursor()
#cursor.execute("select b.bug_id, b.bug_status, b.resolution, cr.statusname \
#				from bugs b \
#					 join crverificationreleasemap map on map.bugid = b.bug_id \
#					 join crverificationstatus cr on cr.id = map.statusid \
#					 join releases r on map.releaseid = r.releaseid \
#				where r.releasenumber >= %s \
#					  and b.bug_status = 'VERIFIED'  \
#					  and b.resolution = 'FIXED' and cr.statusname = 'Open';" % release)
#
#rows            = cursor.fetchall()
#print "rows are: "
#print rows
#cols            = [ d[0] for d in cursor.description ]
#change_requests = dict(zip(cols, row))
#
#ids = [bug[0] for bug in rows]
#
#print
#print ids
#print
#
##ids = [bug['bug_id'] for bug in change_requests['bug_id']]
#
#print 'Bug IDs that need to be modified:\n', ids


#if modify_cr_statuses:
cookie_values = authenticate()
current_release_id = str(current['releaseid'][0])
previous_release_id = str(previous['releaseid'][0])
post_url = 'https://release.akamai.com/release_cr_json.pl'
csv_url  = 'https://release.akamai.com/release_cr_new.pl?releaseid=26851&v=2&m=a&prev_release_id=35400&dump_csv=1'
print current_release_id
cr_file = "%s_crs.csv" % current_release_id
h_sep = "\" -H \""
d_sep = "\" --data \""
h1  = 'Cookie: XR77=3sXfsPplidnve10B7eneOik6YeSDhkjVRmV8lTLXRG8Y8cUL0TBNzeg; \
pubcookie_s_release.akamai.com=' + cookie_values[0] + '; releasegroup=Development; \
default_column_2=bugid%2Cloginname%2Ccomponent%2Cversionvalue%2Cbugdate%2Cshortdescription%2Cpriority%2Cstatus%2Csqa_status%2Cqacontact%2Cis_dep; default_column_sort_2=%5B%22sqa_status%22%2C%22-status%22%5D'
h2  = 'Origin: https://release.akamai.com'
h3  = 'Accept-Encoding: gzip,deflate,sdch'
h4  = 'Host: release.akamai.com'
h5  = 'Accept-Language: en-US,en;q=0.8'
h6  = 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36'
h7  = 'Content-Type: application/x-www-form-urlencoded'
h8  = 'Accept: */*'
h9  = 'Referer: https://release.akamai.com/release_cr_new.html?releaseid=' + current_release_id + '&v=2&m=a&prev_release_id=' + previous_release_id
h10 = 'X-Requested-With: XMLHttpRequest'
h11 = 'Connection: keep-alive'
#headers = [h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11]
url = 'https://release.akamai.com/release_cr_new.pl?releaseid=' + current_release_id + '&v=2&m=a&prev_release_id=' + previous_release_id + '&dump_csv=1'
csv_cmd = "curl -o " + cr_file + " \"" + csv_url + h_sep + h1 + h_sep + h2 + h_sep + h3 + h_sep + h4 + h_sep + h5 + h_sep + h6 + h_sep + h7 + h_sep + h8 + h_sep + h9 + h_sep + h10 + h_sep + h11 + '\"'
#print "command is ", csv_cmd

os.system(csv_cmd)
time.sleep(5)

with open(cr_file, 'r') as f:
  ids = find_bugs(f.readlines())

if args.get_list_only:
  print ids
  exit(0)
for bug_id in ids:
	print bug_id
	d1  = 'dump_json=1&releaseid=' + current_release_id + '&v=2&m=a&prev_release_id=' + previous_release_id + '&bug_ids=' + bug_id + '&set_cols=sqa_status&sqa_updates%5B0%5D%5Bbugid%5D=' + bug_id + '&sqa_updates%5B0%5D%5Bsqa_status%5D=6'
	post_cmd = "curl \"" + post_url + h_sep + h1 + h_sep + h2 + h_sep + h3 + h_sep + h4 + h_sep + h5 + h_sep + h6 + h_sep + h7 + h_sep + h8 + h_sep + h9 + h_sep + h10 + h_sep + h11 + d_sep + d1 + '\"'
	os.system(post_cmd)

