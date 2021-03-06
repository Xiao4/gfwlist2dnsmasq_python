#!/usr/bin/env python  
#coding=utf-8
#  
# Generate a list of dnsmasq rules with ipset for gfwlist
# Ref https://github.com/gfwlist/gfwlist   
 
import urllib2 
import re
import os
import datetime
import base64
import shutil
import ssl
 
mydnsip = '<Your-DNS-Server-IP-HERE>'
mydnsport = '<Your-DNS-Server-PORT-HERE>'
ipsetname = 'gfwlist'
# Extra Domain;
EX_DOMAIN=[ \
'google.com', \
'google.com.hk', \
'google.com.tw', \
'google.com.sg', \
'google.co.jp', \
'google.co.kr', \
'blogspot.com', \
'blogspot.sg', \
'blogspot.hk', \
'blogspot.jp', \
'blogspot.kr', \
'gvt1.com', \
'gvt2.com', \
'gvt3.com', \
'1e100.net', \
'blogspot.tw' \
]
# Excluded domains;
EXCLUDES=[ \
'.m-team.cc' \
]

# the url of gfwlist
baseurl = 'https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt'
# match comments/title/whitelist/ip address
comment_pattern = '^\!|\[|^@@|^\d+\.\d+\.\d+\.\d+'
domain_pattern = '(?:[\w\-]*\*[\w\-]*\.)?([\w\-]+\.[\w\.\-]+)[\/\*]*'
ip_pattern = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
tmpfile = '/tmp/gfwlisttmp'
# do not write to router internal flash directly
outfile = '/tmp/dnsmasq_list.conf'
rulesfile = './dnsmasq_list.conf'
 
fs =  file(outfile, 'w')
fs.write('# gfw list ipset rules for dnsmasq\n')
fs.write('# updated on ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '\n')
fs.write('#\n')
 
print 'fetching list...'
if hasattr(ssl, '_create_unverified_context'):
	ssl._create_default_https_context = ssl._create_unverified_context
content = urllib2.urlopen(baseurl, timeout=15).read().decode('base64')
 
# write the decoded content to file then read line by line
tfs = open(tmpfile+'.before', 'w')
tfs.write(content)
tfs.close()

#exclude domains
print 'remove excluded domains...'
oldfile = open(tmpfile+'.before', 'r')
newfile = open(tmpfile, 'w')

for line in oldfile:
        if not any(exclude in line for exclude in EXCLUDES):
            newfile.write(line)
oldfile.close()
newfile.close()

tfs = open(tmpfile, 'r')
 
print 'page content fetched, analysis...'
 
# remember all blocked domains, in case of duplicate records
domainlist = []

 
for line in tfs.readlines():	
	if re.findall(comment_pattern, line):
		print 'this is a comment line: ' + line
		#fs.write('#' + line)
	else:
		domain = re.findall(domain_pattern, line)
		if domain:
			try:
				found = domainlist.index(domain[0])
				print domain[0] + ' exists.'
			except ValueError:
				if ip_pattern.match(domain[0]):
					print 'skipping ip: ' + domain[0]
					continue
				print 'saving ' + domain[0]
				domainlist.append(domain[0])
				fs.write('server=/%s/%s#%s\n'%(domain[0],mydnsip,mydnsport))
				fs.write('ipset=/%s/%s\n'%(domain[0],ipsetname))
		else:
			print 'no valid domain in this line: ' + line
					
tfs.close()	

for each in EX_DOMAIN:
	fs.write('server=/%s/%s#%s\n'%(each,mydnsip,mydnsport))
	fs.write('ipset=/%s/%s\n'%(each,ipsetname))

print 'write extra domain done'

fs.close();
print 'moving generated file to dnsmasq directory'
shutil.move(outfile, rulesfile)
 
print 'done!'
