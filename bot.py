from bottle import get, post, request, run, template, route, static_file
import os
import requests
import sys
import json
import base64
import webbrowser
from ldap3 import Server, Connection, AUTO_BIND_NO_TLS, SUBTREE, BASE, ALL_ATTRIBUTES, ObjectDef, AttrDef, Reader, Entry, Attribute, OperationalAttribute
import re
import bottle
from collections import Counter

@get('/<filename:re:.*\.css>')

def stylesheets(filename):
    return static_file(filename, root='./')

webbrowser.open('http://localhost:5000/login')
@get('/')
def index():
	return "Please visit the <a href='/login'><b>/login</b></a> page."

@get('/login')
def login_form():
	return '''<link type="text/css" href="component.css" rel="stylesheet">
		<form method="POST" action="/login">
		<table style="width:100%">
		<tr>
		<td>Crowd Admin Name:</td>
		<td><input name="cname"     type="text" /></td></tr>
		<td>Crowd Admin Password:</td>
		<td><input name="cpassword" type="password" /></td></tr>
		<td>Ldap Admin Name:</td>
		<td><input name="lname"     type="text" /></td></tr>
		<td>Ldap Admin Password:</td>
		<td><input name="lpassword" type="password" /></td></tr>
		<td>Ldap group to import:</td>
		<td><input name="lgroup" type="text" /></td></tr>
		<td>Dev (y/n):</td>
		<td><input name="dev" type="text" /></td></tr>
		
	 	<tr><td><input  type="submit" /></td></tr>
		</form>
		<!--<small><i>Hint: try 'admin' and 'admin'</i></small>-->'''

@post('/login')
#@route('/')
#@view('index')
def login_submit():
	cname     = request.forms.get('cname')
	cpassword = request.forms.get('cpassword')
	lname     = request.forms.get('lname')
	lpassword = request.forms.get('lpassword')
	dev = request.forms.get('dev')
	lgroup = request.forms.get('lgroup')

	if check_login(cname, cpassword, dev):
		global crowd
		global ldap
		if dev == "y":  #fake datas
			ldap = ['test@yourdomain.com', 'edo@yourdomain.com', 'gdf@yourdomain.com']
			crowd = ['test@yourdomain.com', 'edo@yourdomain.com', 'tr@ds.com']
			lgroup = "test_group"
		else:

			if lgroup: #must add a users to a group

				print("empty")
			else:  #simple compare between ldap and crowd
				ldap_lookup(lname,lpassword)
				#print (ldap)
				
				crowd_lookup(cname, cpassword)

				
				# Counter method MOVE TO DEF!!!
				c1 = Counter(ldap)
				c2 = Counter(crowd)
				diff = c1-c2
				diff2 = c2-c1

				results = template('make_table', rows=diff) #show users in ldap but not in crowd
				return results
			
	else:
		return "<p>Login failed</p>"
		
#@post('/compare')
#def compare(ldap,crowd):


def check_login(cname, cpassword, dev):
	global tempauth
	if dev == "y":
		return True
	else:
		myauth=(cname + ":" + cpassword)
		bytes_myauth = bytes(myauth, 'utf-8')
		enc_myauth = base64.b64encode(bytes_myauth)
		tempauth = enc_myauth
		tempauth = str(tempauth)
		tempauth = tempauth[1:]
		u = requests.get("https://yourdomain.atlassian.net/rest/api/2/issue/",headers={"Authorization":"Basic {}".format(tempauth),"Content-Type": "application/json"})
		if (u.status_code == 200):

			return True
		else:
			return False
			
    
    
    

@post('/results')
def diplay_results():

	return 	'''<form method="POST" action="/results">
		<p>Your results</p>
		'''

def ldap_lookup(lname,lpassword):
	global ldap	
	#ldap
	server = "yourLDAPdomain"
	bname = lname + "@yourdomain.com"
	c = Connection(server, user=bname, password=lpassword, auto_bind=True, raise_exceptions=False)
	c.search('ou=yourOU,dc=yourdomain,dc=loc', '(&(objectCategory=person)(objectClass=User)(givenname=*))', attributes=['mail'])
	emaillist = str(c.entries)
	ldap = re.findall(r'[\w\.-]+@[\w\.-]+', emaillist)
	#ldap2 = []
	#ldap2.append(ldap)
	return ldap
	
def ldap_lookup_group(lname,lpassword,lgroup):
	global ldap_group_users
	#ldap
	server = "yourLDAPdomain"
	bname = lname + "@yourdomain.com"
	c = Connection(server, user=bname, password=lpassword, auto_bind=True, raise_exceptions=False)

	#c.search('ou=yourOU,dc=yourdomain,dc=com', '(&(objectCategory=person)(objectClass=User)(givenname=*) &(memberof=cn={},dc=foo,dc=bar) ', attributes=['mail']).format(lgroup)

	c.search('ou=yourOU,dc=yourdomain,dc=com', '(&(objectCategory=person)(objectClass=User)(memberof=CN={},OU=otherRelevantOU,OU=yourOU,DC=yourdomain,DC=com))'.format(lgroup), attributes=['mail'])

	emaillist = str(c.entries)
	ldap_group_users = re.findall(r'[\w\.-]+@[\w\.-]+', emaillist)
	#ldap2 = []
	#ldap2.append(ldap)

	return ldap_group_users

def crowd_import_group(cname,cpassword,lgroup):
	global ldap_group_users;
	#global lgroup;
	myauth=(cname + ":" + cpassword)
	bytes_myauth = bytes(myauth, 'utf-8')
	enc_myauth = base64.b64encode(bytes_myauth)
	tempauth = enc_myauth
	tempauth = str(tempauth)
	tempauth = tempauth[1:]
	url='https://yourdomain.atlassian.net'
	groupRestUrl = '%s/rest/api/2/group' % (url)
	headers={"Authorization":"Basic {}".format(tempauth), "Content-Type": "application/json"}
	params = {"name": "{}"}.format(lgroup)
	addUsersRestUrl = '%s/rest/api/2/group/user?groupname=%s' % (url, lgroup) 
	
	
	# create group
	response = requests.post(groupRestUrl, data=params, headers=headers)

	# add users to group
	for x in ldap_group_users:
		params2 = '{"name": %s}' % (x)
		y = requests.post(addUsersRestUrl, data=params2, headers=headers)
		response += y.text

	#set(tuple(element) for element in crowd)
	#ar=[list(t) for t in set(tuple(element) for element in crowd)]
	return response

def crowd_lookup(cname, cpassword):
	global crowd

	# jira
	crowd=[]
	a = list(map(chr, range(ord('a'), ord('z') + 1))) # ['a','z'] #
	
	myauth=(cname + ":" + cpassword)
	bytes_myauth = bytes(myauth, 'utf-8')
	enc_myauth = base64.b64encode(bytes_myauth)
	tempauth = enc_myauth
	tempauth = str(tempauth)
	tempauth = tempauth[1:]

	
	#printauth = (str(tempauth) + "\n" + str(tempauth2))
	for x in a:
		y=requests.get("https://yourdomain.atlassian.net/rest/api/2/user/search",params={'username':x},headers={"Authorization":"Basic {}".format(tempauth),"Content-Type": "application/json"})
		for i in y.json():
			array=i['emailAddress']
			crowd.append(array)

	#set(tuple(element) for element in crowd)
	#ar=[list(t) for t in set(tuple(element) for element in crowd)]
	return crowd

@route('/adduser/<emailaddress>')
#@route('/')
#@view('index')
def adduser(emailaddress):
	global tempauth
	newuser = emailaddress.rsplit('@', 1)[0]
	groupname = "confluence-users"
	headers= {"Authorization":"Basic {}".format(tempauth), "Content-Type": "application/json"}
	params = { 
	"name":newuser,
	"password":"xxx",
	"emailAddress":emailaddress,
	"displayName":newuser,
	"notification":"false" 
	}
	url='https://yourdomain.atlassian.net'
	restUrl = '%s/rest/api/2/user' % (url)
	params = json.dumps(params)

	paramsGroup = {"name": newuser}
	paramsGroup = json.dumps(paramsGroup)
	restUrlGroup = '%s/rest/api/2/group/user?groupname=%s' % (url, groupname)

	response = requests.post(restUrl, data=params, headers=headers)
	responseGroup = requests.post(restUrlGroup, data=paramsGroup, headers=headers)

	#print (response)
	#print (restUrl)
	#print (params)

	#print (responseGroup)
	#print (restUrlGroup)
	#print (paramsGroup)


	results = "Done. Add user response is %s. Add users to confluence response is %s" % (response.status_code, responseGroup.status_code)
	return results	

		
run(debug=True, reloader=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
		
