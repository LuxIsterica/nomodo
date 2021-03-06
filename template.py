import sys
sys.path.append('systemcalls')
from user import getusers, getuser, getgroups, getshells, updateusershell, getusernotgroups, getusergroups, addusertogroups, removeuserfromgroups, updateuserpass, adduser, removeuser
from apps import listinstalled, aptsearch, aptshow, getreponame, addrepo, removerepofile, getexternalrepos, aptupdate, aptremove, aptinstall
from apps import externalreposdir
from systemfile import locate,updatedb
from system import getsysteminfo, hostname
from network import ifacestat, getnewifacealiasname, createalias, destroyalias, ifaceup,ifacedown
from apache import apachestart, apachestop, apacherestart, apachereload, apachestatus, getvhosts, getmods, getconf, activatevhost, deactivatevhost, activatemod, deactivatemod, activateconf, deactivateconf
from apache import apacheconfdir
from cron import listcrontabs, addcron, addhourlycron, adddailycron, addweeklycron, addmonthlyycron, getcronname
from utilities import readfile, writefile, filedel, filecopy, filerename, readdir, mongocheck, mongostart
from logs import getlog

from flask import Flask, render_template, flash, request, redirect, url_for, jsonify

from flask_bootstrap import Bootstrap

app = Flask(__name__, template_folder = "templates", static_folder = "static", static_url_path = "/static")
app.secret_key = 'random string'
bootstrap = Bootstrap(app)


########## FUNZIONALITÀ user.py ##########

# http://localhost:5000/listUser/
@app.route('/listUserAndGroups')
def listUserAndGroups():
	error = None
	users = getusers()
	groups = getgroups()
	shells = getshells()
	if users['returncode'] != 0 or groups['returncode'] != 0:
		flash("getusers or getgroups failed")
	else:
		return render_template('users.html', users = users,groups = groups,shells = shells)
	return redirect(url_for('listUserAndGroups'))

# http://localhost:5000/getInfoUser/<clicca valore uname>
@app.route('/getInfoUser/<string:uname>')
def getInfoUser(uname):
	infouser = getuser(uname)
	shells = getshells()
	nogroups = getusernotgroups(uname)
	groupsuser = getusergroups(uname)
	return render_template('info-user.html', infouser = infouser, shells = shells, nogroups = nogroups, groupsuser=groupsuser)

@app.route('/updateShell', methods=['POST'])
def updateShell():
	try:
		error = None
		uname = request.form['unameUpdate'];
		shell = request.form['newShell'];
		if shell == '-- Seleziona nuova shell --':
			error = 'Invalid option'
		else:
			log = updateusershell(uname, shell)
			if(log['returncode'] != 0):
				error = log['stderr']
			else:
				flash('Shell changed correctly!')	
				return redirect(url_for('listUserAndGroups'))
		return render_template('users.html',error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/addUserGroup', methods=['POST'])
def addUserGroup():
	try:
		error = None
		uname = request.form['unameAdd'];
		moreGr = request.form.getlist('moreGroups');
		if not uname:
			error = "uname empty"
			return render_template("users.html",error=error)
		else:
			if '-- Seleziona uno o più gruppi --' in moreGr:
				flash('Invalid option')
			else:
				log = addusertogroups(uname, *moreGr)
				if(log['returncode'] != 0):
					flash(log['stderr'])
				else:
					flash('User added correctly to groups!')
		return redirect(url_for('listUserAndGroups'))
	except Exception:
		return internal_server_error(500)

@app.route('/removeUserGroup', methods=['POST'])
def removeUserGroup():
	try:
		error = None
		uname = request.form['unameRem'];
		moreGr = request.form.getlist('moreGroups');
		if not uname:
			error = "uname empty"
			return render_template("users.html",error=error)
		else:
			if '-- Seleziona uno o più gruppi --' in moreGr:
				flash('Invalid option')
			else:
				log = removeuserfromgroups(uname, *moreGr)
				if(log['returncode'] != 0):
					flash(log['stderr'])
				else:
					flash('User deleted correctly to groups!')
		return redirect(url_for('listUserAndGroups'))
	except Exception:
		return internal_server_error(500)

@app.route('/updateUserPwd', methods=['POST'])
def updateUserPwd():
	try:
		error = None
		uname = request.form['uname']
		newPwd = request.form['newPassword']
		if not newPwd:
			flash('Password empty')
		else:
			log = updateuserpass(uname, newPwd)
			if(log['returncode'] != 0):
				flash(log['stderr'])
			else:
				flash('Password updated correctly')
		
		return redirect(url_for('listUserAndGroups'))
	except Exception:
		return internal_server_error(500)

@app.route('/addUser', methods=['POST'])
def addUser():
	error = None
	user = request.form['user']
	pwd = request.form['password']
	shell = request.form['shell']
	if not user and not password:
		error = 'User and password empty'
		return render_template('listUserAndGroups',error=error)
	else:
		log = adduser(user,pwd,shell)
		if(log['returncode'] != 0):
			error = log['stderr']
			return render_template('listUserAndGroups',error=error)
		else:
			flash('User added correctly!')
	return redirect(url_for('listUserAndGroups'))

@app.route('/removeUser', methods=['POST'])
def removeUser():
	error = None
	user = request.form['user']
	if not user:
		error = 'User empty'
		return render_template('listUserAndGroups',error=error)
	else:
		log = removeuser(user)
		if(log['returncode'] != 0):
			flash(log['stderr'])
		else:
			flash('User deleted correctly!')
	return redirect(url_for('listUserAndGroups'))

########## FUNZIONALITÀ cron.py ##########

@app.route('/listCron')
def listCron():
	listCrontabs = listcrontabs()
	generatedCronName = getcronname()
	return render_template("jobs.html",listCrontabs=listCrontabs, generatedCronName=generatedCronName)

@app.route('/getContentCrontab/<string:cronk>/<string:cronv>')
def getContentCrontab(cronk,cronv):
	basedir='/etc/'
	pathCron=basedir+cronk+'/'+cronv
	content = readfile(pathCron)
	#return send_file(pathCron,attachment_filename=cronv) fa il download
	return render_template("jobs-details.html", content=content, pathCron=pathCron)

@app.route('/updateCrontab', methods=['POST'])
def updateCrontab():
	try:
		error = None
		updatedCrontab = request.form['contentTextarea']
		path = request.form['hiddenPath']
		if not updateCrontab and not path:
			error = "Errore passaggio parametri: vuoti"
			return render_template("jobs.html", error=error)
		else:
			newPath = writefile(path, updatedCrontab)
			if(newPath['returncode'] != 0):
				error = "Edit cron failed"
				return render_template("jobs.html", error=error)
			else:
				flash("Cron updated correctly")
				return redirect(url_for('listCron'))
	except Exception:
		return internal_server_error(500)	

@app.route('/deleteCron', methods=['POST'])
def deleteCron():
	try:
		error = None
		selectedCron = request.form['selectedCron']
		basedir='/etc/'
		pathCron=basedir+selectedCron
		if not selectedCron:
			error = "No cron selected"
			return render_template("jobs.html",error=error)
		else:
			if selectedCron == '-- Seleziona cron --':
				flash('Invalid option')
			else:
				log = filedel(pathCron)
				if(log['returncode'] != 0):
					flash(log['stderr'])
				else:
					flash('Cron deleted correctly!')

			return redirect(url_for('listCron'))
	except Exception:
		return internal_server_error(500)

@app.route('/addCron', methods=['POST'])
def addCron():
	try:
		error = None
		command=request.form["command"] 
		name=request.form["nameCron"] 
		user=request.form["user"] 
		minute=request.form["minute"] 
		hour=request.form["hour"] 
		dom=request.form["dayOfMounth"] 
		month=request.form["mounth"] 
		dow=request.form["dayOfWeek"]
		if not command:
			error = "Command cannot be empty"
		else:
			log = addcron(command, name, user, minute, hour, dom, month, dow)
			if log['returncode'] != 0:
				error = "Add cron failed"
			else:
				flash("Cron added correctly")
				return redirect(url_for('listCron'))
		return render_template("jobs.html",error=error)	
	except Exception:
		return internal_server_error(500)

@app.route('/addCustomCron', methods=['POST'])
def addCustomCron():
	try:
		error = None
		command=request.form["command"] 
		name=request.form["nameCron"]
		typeOption = request.form["typeOption"]
		if not command:
			error = "Command cannot be empty"
		else:
			if typeOption == 'ogni ora':
				log = addhourlycron(command, name)
			elif typeOption == 'ogni giorno':
				log = adddailycron(command, name)
			elif typeOption == 'ogni settimana':
				log = addweeklycron(command, name)
			elif typeOption == 'ogni mese':
				log = addmonthlyycron(command, name)

			if log['returncode'] != 0:
				error = "Add cron failed"
			else:
				flash("Cron custom added correctly")
				return redirect(url_for('listCron'))
		return render_template("jobs.html",error=error)	
	except Exception:
		return internal_server_error(500)

########## FUNZIONALITÀ apps.py ##########

# http://localhost:5000/listInstalled
@app.route('/listInstalled')
def listInstalled():
	listAppInst = listinstalled(True)
	return render_template('applications.html', listAppInst = listAppInst)

@app.route('/findPkg', methods=['POST'])
def findPkg():
	error = None
	pkg = request.form['pkgSearch']
	if not pkg:
		flash(u'Wrong operation, impossible to search empty string','warning')
	else:
		if request.form.get('filterName') is not None:
			appFound = aptsearch(pkg)
			return render_template('find-pkg.html', appFound = appFound)
		else:
			appFound = aptsearch(pkg,namesonly=False)
			return render_template('find-pkg.html', appFound = appFound)
	return redirect(url_for('listInstalled'))
	

@app.route('/getInfoApp/<string:name>')
def getInfoApp(name):
	infoApp = aptshow(name)['data']
	#infoApp = infoApp.replace('\n', '<br>')
	return render_template('info-app.html', infoApp = infoApp, name = name)

@app.route('/removePackage/<string:name>')
def removePackage(name):
	log = aptremove(name, False)
	if log['returncode'] != 0:
		error = 'Error package deletion failed'
	else:
		flash(u'Package removed correctly!','success')
		return redirect(url_for('listInstalled'))
	return render_template('applications.html',error=error)

@app.route('/installPackage/<string:name>')
def installPackage(name):
	log = aptinstall(name)
	if log['returncode'] != 0:
		error = 'Error package installation failed'
	else:
		flash(u'Package installed correctly!','success')
		return redirect(url_for('listInstalled'))
	return render_template('applications.html',error=error)

@app.route('/retrieveExternalRepo')
def retrieveExternalRepo():
	listOtherRepo = getexternalrepos()['data']
	generatedRepoName = getreponame()
	return render_template("other-repo.html", listOtherRepo=listOtherRepo, generatedRepoName=generatedRepoName)

@app.route('/addRepo', methods=['POST'])
def addRepo():
	try:
		error = None
		contentRepo = request.form['contentTextarea']
		repoName = request.form['nameRepo']
		log = addrepo(contentRepo,repoName)
		if log['returncode'] != 0:
			error = 'Repository added failed'
			return render_template('applications.html',error=error)
		else:
			flash(u'Repository added correctly!','success')
			return redirect(url_for('retrieveExternalRepo'))
	except Exception:
		return internal_server_error(500)

@app.route('/getContentRepo', methods=['POST'])
def getContentRepo():
	error = None
	filenameSelected = request.form['filenameSelected']
	if not filenameSelected:
		error = "No file selected"
		return render_template("other-repo.html",error=error)
	else:
		if filenameSelected == '-- Seleziona il filename --':
			flash('Invalid option')
		else:
			pathRepo = externalreposdir + filenameSelected
			content = readfile(pathRepo)
			if(content['returncode'] != 0):
				flash(log['stderr'])
			else:
				return render_template('other-repo-content.html',pathRepo=pathRepo,content=content)
		
	return redirect(url_for('retrieveExternalRepo'))

@app.route('/updateRepoFile', methods=['POST'])
def updateRepoFile():
	#try:
		error = None
		updatedRepo = request.form['contentTextarea']
		path = request.form['pathRepo']
		if not updatedRepo and not path:
			error = "Parameters empty"
			return render_template("other-repo.html", error=error)
		else:
			newPath = writefile(path, updatedRepo)
			if(newPath['returncode'] != 0):
				error = "Updated repository failed"
				return render_template("other-repo.html", error=error)
			else:
				flash("Change successful!")
				return redirect(url_for('retrieveExternalRepo'))
	#except Exception:
	#	return internal_server_error(500)

@app.route('/removeRepo', methods=['POST'])
def removeRepo():
	#try:
	error = None
	filenameSelected = request.form['filenameSelected']
	if not filenameSelected:
		error = "No file selected"
		return render_template("other-repo.html",error=error)
	else:
		if '.list' in filenameSelected:
			newFilenameSelected = filenameSelected.replace('.list','')
		if '.list.save' in filenameSelected:
			newFilenameSelected = filenameSelected.replace('.list.save','')
		else:
			newFilenameSelected = filenameSelected

		if newFilenameSelected == '-- Seleziona il filename --':
			flash('Invalid option')
		else:
			log = removerepofile(newFilenameSelected)
			if(log['returncode'] != 0):
				flash(log['stderr'])
			else:
				flash('Repository deleted correctly!')
		flash(newFilenameSelected)
		return redirect(url_for('retrieveExternalRepo'))
	#except Exception:
	#	return internal_server_error(500)

@app.route('/aggiornaCachePacchetti', methods=['POST'])
def aggiornaCachePacchetti():
	try:
		error = None
		if request.form['aggiornaCachePacchetti'] == 'Aggiorna cache pacchetti':
			log = aptupdate()
			if(log['returncode'] != 0):
				flash(log['stderr'])
				return redirect(url_for('retrieveExternalRepo'))
			else:
				flash('Cache packages updated!')
				return redirect(url_for('retrieveExternalRepo'))
		else:
			error = 'Non funzica' 
		return render_template('other-repo.html', error=error)
	except Exception:
		return internal_server_error(500)

########## FUNZIONALITÀ systemfile.py ##########

@app.route('/file')
def file():
	return render_template('file.html')

@app.route('/findFile', methods=['POST'])
def findFile():
	error = None
	fs = request.form['fileSearch'];
	if not fs:
		flash(u'Impossible to search empty string','error')
	else:
		pathFileFound = locate(fs);
		if not pathFileFound:
			error = "No file found"
			return render_template('file.html',error=error)
		else:
			return render_template('file.html', pathFileFound = pathFileFound)
		
	return redirect(url_for('file'))

@app.route('/updateDbFile', methods=['POST'])
def updateDbFile():
	try:
		error = None
		if request.form['updateDbFile'] == 'Aggiorna DB File':
			log = updatedb()
			if(log['returncode'] != 0):
				error = 'File database not updated'
				return render_template('file.html',error=error)
			else:
				flash(u'Db updated!','info')
				return redirect(url_for('file'))
		else:
			error = 'Non funzica' 
		return render_template('file.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/retriveContentFile', methods=['POST'])
def retriveContentFile():
	try:
		error = None
		if request.form['retriveContentFile'] == 'Modifica':
			pathFile = request.form['pathFile']
			if not pathFile:
				error = "Path empty"
				return render_template("file.html",error=error)
			else:
				fileContent = readfile(pathFile)
				if(fileContent['returncode'] != 0):
					error = fileContent['command']
				else:
					return render_template("file-content.html", fileContent=fileContent, pathFile=pathFile)
		else:
			error = 'Non funzica' 
		return render_template('file.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/updateFile', methods=['POST'])
def updateFile():
	try:
		error = None
		pathFile = request.form['pathFile']
		updatedContentFile = request.form['contentTextarea']
		newContent = writefile(pathFile,updatedContentFile)
		if(newContent['returncode'] != 0):
			error = "Error during modification"
			return render_template("file.html",error=error)
		else:
			flash(u'Change successful!!','info')
			return redirect(url_for('file'))
	except Exception:
		return internal_server_error(500)

@app.route('/deleteFile', methods=['POST'])
def deleteFile():
	try:
		error = None
		if request.form['deleteFile'] == 'Elimina':
			pathFile = request.form['pathFile']
			if not pathFile:
				error = "Path empty"
				return render_template("file.html",error=error)
			else:
				log = filedel(pathFile)
				if(log['returncode'] != 0):
					error = log['stderr']
					return render_template('file.html',error=error)
				else:
					log = updatedb()
					if(log['returncode'] != 0):
						error = 'File database not updated'
						return render_template('file.html',error=error)
					else:
						flash(u'File deleted correctly!','info')
						return redirect(url_for('file'))
		else:
			error = 'Non funzica' 
		return render_template('file.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/copyFile', methods=['POST'])
def copyFile():
	error = None
	if request.form['copyFile'] == 'Copia':
		pathFile = request.form['pathFile']
		pathDest = request.form['destPathFile']
		if not pathFile:
			error = "Path empty"
			return render_template("file.html",error=error)
		elif not pathDest:
			error = "Destination path cannot be empty"
			return render_template("file.html",error=error)
		else:
			log = filecopy(pathFile,pathDest)
			if(log['returncode'] != 0):
				error =	log['stderr']
				return render_template("file.html",error=error)
			else:
				log = updatedb()
				if(log['returncode'] != 0):
					error = 'Database dei file non aggiornato'
					return render_template('file.html',error=error)
				else:
					flash(u'File copiato correctly!','info')
					return redirect(url_for('file'))
	else:
		error = 'Non funzica'	

@app.route('/renameFile', methods=['POST'])
def renameFile():
	error = None
	if request.form['renameFile'] == 'Rinomina':
		pathFile = request.form['pathFile']
		newName = request.form['newNameFile']
		if not pathFile:
			error = "Path empty"
			return render_template("file.html",error=error)
		elif not newName:
			error = "Nessun nuovo nome inserito"
			return render_template("file.html",error=error)
		else:
			log = filerename(pathFile,newName)
			if(log['returncode'] != 0):
				error =	log['stderr']
				return render_template("file.html",error=error)
			else:
				log = updatedb()
				if(log['returncode'] != 0):
					error = 'Database dei file non aggiornato'
					return render_template('file.html',error=error)
				else:
					flash(u'File rinominato correctly!','info')
					return redirect(url_for('file'))
	else:
		error = 'Non funzica'
		return render_template("file.html",error=error)

########## FUNZIONALITÀ system.py ##########
#http://localhost:5000/dash
# definizione base dash con componente fissa navbar
@app.route('/dash')
def dash():
	tpl = getsysteminfo()
	(cpu,mem,proc) = tpl['data']
	return render_template('dash.html', cpu = cpu, mem = mem, proc = proc)

@app.route('/param')
def param():
	error = None
	hname = hostname()
	listFile = list()
	listDir = list()
	listFile = ['/etc/hosts','/etc/apache2/apache2.conf','/etc/profile','/etc/motd','/etc/network/interfaces','/etc/crontab']
	listDir = ['/etc/apache2/sites-available','/etc/apache2/mods-available','etc/apache2/conf-available','/etc/update.motd.d/','/etc/network/interfaces.d/','/var/spool/cron/crontabs']
	if(hname['returncode'] != 0):
		flash(hname['stderr'])
	else:
		return render_template('param.html', hname=hname, listFile=listFile, listDir=listDir)
	return render_template('param.html')

@app.route('/newHostname', methods=['POST'])
def newHostname():
	try:
		error = None
		hname = request.form['newHname']
		if not hname:
			flash('Hostname cannot be empty!')
		else:
			log = hostname(hname)
			if(log['returncode'] != 0):
				flash(log['stderr'])
			else:
				flash('Hostname changed correctly!')
		return redirect(url_for('param'))
	except Exception:
		return internal_server_error(500)

@app.route('/retriveFileDir', methods=['POST'])
def retriveFileDir():
	pathDir = request.form['pathDir']
	if not pathDir:
		flash('Path directory is empty')
	else:
		listFile = readdir(pathDir)
		if listFile['returncode'] != 0:
			flash(log['stderr'])
		else:
			return render_template("dir-content.html", listFile=listFile, pathDir=pathDir)
	return redirect(url_for('param'))

########## FUNZIONALITÀ network.py ##########
@app.route('/network')
def network():
	key_remove = list()
	lo = dict()
	als = dict()
	faceUp = dict()
	faceDown = dict()
	facestat = ifacestat()['data']
	for key,value in facestat.items():
		if 'LOOPBACK' in value[-1]:
			lo.update({key:facestat[key]})
			key_remove.append(key)
		elif ':' in key:
			als.update({key:facestat[key]})
			key_remove.append(key)

	for key in key_remove:
		del facestat[key]
	
	for key, value in facestat.items():
		if not 'UP' in value[-1]:
			facestat[key].append('DOWN')
	return render_template('network.html', facestat=facestat, lo=lo, als=als)

@app.route('/createAlias', methods=['POST'])
def createAlias():
	try:
		error = None
		iface = request.form['iface']
		address = request.form['address']
		netmask = request.form['netmask']
		broadcast = request.form['broadcast']
		if not iface or iface == '-- Seleziona interfaccia --':
			error = 'Invalid option'
		else:
			generatedAliasName = getnewifacealiasname(iface)
			if not address:
				error = 'Address empty'
			else:
				log = createalias(generatedAliasName['data'],address,netmask,broadcast)
				if(log['returncode'] != 0):
					error = log['stderr']
				else:
					flash("Alias created correctly")
					return redirect(url_for('network'))
		return render_template('network.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/destroyAlias', methods=['POST'])
def destroyAlias():
	try:
		error = None
		alias = request.form['alias']
		if not alias or alias == '-- Seleziona alias --':
			error = 'Invalid option'
		else:
			log = destroyalias(alias)
			if(log['returncode'] != 0):
				error = log['stderr']
			else:
				flash("Alias deleted correctly")
				return redirect(url_for('network'))
		return render_template('network.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/upIface', methods=['POST'])
def upIface():
	iface = request.form['iface']
	address = request.form['address']
	netmask = request.form['netmask']
	broadcast = request.form['broadcast']
	facestat = ifacestat()['data']
	if '-- Seleziona interfaccia --' in iface:
		flash('Invalid option')
	else:
		if iface in facestat:
			log = ifaceup(iface)
			if(log['returncode'] != 0):
				error = log['stderr']
			else:
				flash("Interface up!")
				return redirect(url_for('network'))			
	return render_template('network.html', error=error)


@app.route('/downIface/<string:iface>', methods=['POST'])
def downIface(iface):
	error = None
	if request.form['down'] == 'Spegni':
		log = ifacedown(iface)
		if(log['returncode'] != 0):
			error = log['stderr']
		else:
			flash('Interface down!')
			return redirect(url_for('network'))
	else:
		error = 'Non funzica' 
	return render_template('network.html', error=error)

########## FUNZIONALITÀ apache.py ##########

@app.route('/startApache', methods=['POST'])
def startApache():
	try:
		error = None
		if request.form['b-start-a'] == 'Start':
			log = apachestart()
			if(log['returncode'] != 0):
				error = log['stderr']
			else:
				flash("Apache started correctly")
				return redirect(url_for('sites'))
		else:
			error = 'Non funzica' 
		return render_template('apache-sites.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/stopApache', methods=['POST'])
def stopApache():
	try:
		error = None
		if request.form['b-stop-a'] == 'Stop':
			log = apachestop()
			if(log['returncode'] != 0):
				error = log['stderr']
			else:
				flash("Apache stopped correctly")
				return redirect(url_for('sites'))
		else:
			error = 'Non funzica' 
		return render_template('apache-sites.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/restartApache', methods=['POST'])
def restartApache():
	try:
		error = None
		if request.form['b-restart-a'] == 'Restart':
			log = apacherestart()
			if(log['returncode'] != 0):
				error = log['stderr']
			else:
				flash("Apache restarted correctly")
				return redirect(url_for('sites'))
		else:
			error = 'Non funzica' 
		return render_template('apache-sites.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/reloadApache', methods=['POST'])
def reloadApache():
	try:
		error = None
		if request.form['b-reload-a'] == 'Reload':
			log = apachereload()
			if(log['returncode'] != 0):
				error = log['stderr']
			else:
				flash("Apache reloaded correctly")
				return redirect(url_for('sites'))
		else:
			error = 'Non funzica' 
		return render_template('apache-sites.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/statusApache', methods=['POST'])
def statusApache():
	try:
		error = None
		if request.form['b-status-a'] == 'Status':
			logStatus = apachestatus()
			if(logStatus['returncode'] != 0):
				error = logStatus['stderr']
			else:
				return render_template('apache-sites.html', logStatus=logStatus)
		else:
			error = 'Non funzica' 
		return render_template('apache-sites.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/sites')
def sites():
	error=None
	vhost=getvhosts()
	if(vhost['returncode'] != 0):
		flash(vhost['stderr'])
		return redirect(url_for('sites'))
	else:
		return render_template('apache-sites.html', vhost=vhost)

@app.route('/retrieveContentSite', methods=['POST'])
def retrieveContentSite():
	nameSite = request.form['retrieveCS']
	contentVhost = readfile(apacheconfdir+"sites-available/"+nameSite)
	return render_template('apache-site-content.html', contentVhost=contentVhost, nameSite=nameSite)

@app.route('/updateContentSite/<string:nameSite>', methods=['POST'])
def updateContentSite(nameSite):
	try:
		error = None
		updatedContentVhost = request.form['contentTextarea']
		newContent = writefile(apacheconfdir+"sites-available/"+nameSite,updatedContentVhost)
		if(newContent['returncode'] != 0):
			error = "Error during modification"
			return render_template('apache-sites.html',error=error)
		else:
			flash("Change successful!")
			return redirect(url_for('sites'))
	except Exception:
		return internal_server_error(500)

@app.route('/modules')
def modules():
	error=None
	mods=getmods()
	if(mods['returncode'] != 0):
		error = mods['stderr']
		return redirect(url_for('sites'))
	else:
		return render_template('apache-modules.html', mods=mods)
	return render_template('apache-modules.html', error=error)

@app.route('/retrieveContentModule', methods=['POST'])
def retrieveContentModule():
	nameMods = request.form['retrieveCM']
	contentMods = readfile(apacheconfdir+"mods-available/"+nameMods)
	return render_template('apache-module-content.html', contentMods=contentMods, nameMods=nameMods)

@app.route('/updateContentMods/<string:nameMods>', methods=['POST'])
def updateContentMods(nameMods):
	try:
		error = None
		updatedContentMods = request.form['contentTextarea']
		newContent = writefile(apacheconfdir+"mods-available/"+nameMods,updatedContentMods)
		if(newContent['returncode'] != 0):
			error = "Error during modification"
			return render_template('apache-modules.html',error=error)
		else:
			flash("Change successful!")
			return redirect(url_for('modules'))
	except Exception:
		return internal_server_error(500) 

@app.route('/configurations')
def configurations():
	error=None
	conf=getconf()
	if(conf['returncode'] != 0):
		error = conf['stderr']
		return redirect(url_for('sites'))
	else:
		return render_template('apache-configurations.html', conf=conf)

	return render_template('apache-configurations.html',error=error)

@app.route('/retrieveContentConfiguration', methods=['POST'])
def retrieveContentConfiguration():
	nameConf = request.form['retrieveCC']
	contentConf = readfile(apacheconfdir+"conf-available/"+nameConf)
	return render_template('apache-configuration-content.html', contentConf=contentConf, nameConf=nameConf)

@app.route('/updateContentConf/<string:nameConf>', methods=['POST'])
def updateContentConf(nameConf):
	try:
		error = None
		updatedContentConf = request.form['contentTextarea']
		newContent = writefile(apacheconfdir+"conf-available/"+nameConf,updatedContentConf)
		if(newContent['returncode'] != 0):
			error = "Error during modification"
			return render_template('apache-configurations.html',error=error)
		else:
			flash("Change successful!")
			return redirect(url_for('configurations'))
	except Exception:
		return internal_server_error(500) 

#creating a view function without returning a response in Flask
# return HTTP/1.1" 204
@app.route('/activateVHost', methods=['POST'])
def activateVHost():
	filename = request.form['clickActiv']
	if filename:
		logAVHost=activatevhost(filename)
		if(logAVHost['returncode'] != 0):
			flash(logAVHost['stderr'])
			#return redirect(url_for('sites'))
			return '',204
	#return redirect(url_for('sites'))
	return '',204 #ritorno senza reindirizzamento con flask

@app.route('/deactivateVHost', methods=['POST'])
def deactivateVHost():
	filename = request.form['clickDeactiv']
	if filename:
		logDAVHost=deactivatevhost(filename)
		if(logDAVHost['returncode'] != 0):
			flash(logDAVHost['stderr'])
			#return redirect(url_for('sites'))
			return '',204
	#return redirect(url_for('sites'))
	return '',204 #ritorno senza reindirizzamento con flask

@app.route('/activateMods', methods=['POST'])
def activateMods():
	filename = request.form['clickActiv']
	if filename:
		logAMod=activatemod(filename)
		if(logAMod['returncode'] != 0):
			flash(logAMod['stderr'])
			#return redirect(url_for('sites'))
			return '',204
	#return redirect(url_for('sites'))
	return '',204 #ritorno senza reindirizzamento con flask

@app.route('/deactivateMods', methods=['POST'])
def deactivateMods():
	filename = request.form['clickDeactiv']
	if filename:
		logDAMod=deactivatemod(filename)
		if(logDAMod['returncode'] != 0):
			flash(logDAMod['stderr'])
			#return redirect(url_for('sites'))
			return '',204
	#return redirect(url_for('sites'))
	return '',204 #ritorno senza reindirizzamento con flask

@app.route('/activateConf', methods=['POST'])
def activateConf():
	filename = request.form['clickActiv']
	if filename:
		logAConf=activateconf(filename)
		if(logAConf['returncode'] != 0):
			flash(logAConf['stderr'])
			#return redirect(url_for('sites'))
			return '',204
	#return redirect(url_for('sites'))
	return '',204 #ritorno senza reindirizzamento con flask

@app.route('/deactivateConf', methods=['POST'])
def deactivateConf():
	filename = request.form['clickDeactiv']
	if filename:
		logDAConf=deactivateconf(filename)
		if(logDAConf['returncode'] != 0):
			flash(logDAConf['stderr'])
			#return redirect(url_for('sites'))
			return '',204
	#return redirect(url_for('sites'))
	return '',204 #ritorno senza reindirizzamento con flask

########## FUNZIONALITÀ logs.py ##########
@app.route('/logs')
def logs():
	logs = getlog()
	return render_template('logs.html',logs=logs)

@app.route('/filtraLog', methods=['POST'])
def filtraLog():
	idLog = request.form['idLog']
	nomeFunzione = request.form['nomeFunzione']
	statoOperazione = request.form['statoOperazione']
	dataDa = request.form['dataDa']
	dataA = request.form['dataA']
	logs = getlog(idLog,nomeFunzione,statoOperazione,dataDa,dataA)
	return render_template('logs.html',logs=logs)

########### CHECK MONGODB ###########

@app.route('/startMongo', methods=['POST'])
def startMongo():
	try:
		error = None
		if request.form['startMongo'] == 'Start Mongo':
			log = mongostart()
			if(log['returncode'] != 0):
				error = log['stderr']
				return render_template('mongo.html',error=error)
			else:
				return redirect(url_for('dash'))
		else:
			error = 'Non funzica' 
			return render_template('mongo.html', error=error)
	except Exception:
		return internal_server_error(500)


@app.before_request
def before_request():
	if request.endpoint != 'startMongo':
		log = mongocheck()
		if(log['returncode'] == 42):
			error = log['stderr']
			return render_template('mongo.html',error=error)


########## GESTIONE ERRORI ##########
 
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
	app.run(debug = True)
